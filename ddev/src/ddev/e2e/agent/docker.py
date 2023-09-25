# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from __future__ import annotations

import os
from functools import cached_property
from typing import TYPE_CHECKING, Any

from ddev.e2e.agent.interface import AgentInterface

if TYPE_CHECKING:
    import subprocess

    from ddev.utils.fs import Path


class DockerAgent(AgentInterface):
    @cached_property
    def _container_name(self) -> str:
        return f'dd_{self.get_id()}'

    @cached_property
    def _is_windows_container(self) -> bool:
        return self.metadata.get('docker_platform') == 'windows'

    @cached_property
    def _package_mount_dir(self) -> str:
        return 'C:\\Users\\ContainerAdministrator\\' if self._is_windows_container else '/home/'

    @cached_property
    def _config_mount_dir(self) -> str:
        return (
            f'C:\\ProgramData\\Datadog\\conf.d\\{self.integration.name}.d'
            if self._is_windows_container
            else f'/etc/datadog-agent/conf.d/{self.integration.name}.d'
        )

    @cached_property
    def _python_path(self) -> str:
        return (
            f'C:\\Program Files\\Datadog\\Datadog Agent\\embedded{self.python_version[0]}\\python.exe'
            if self._is_windows_container
            else f'/opt/datadog-agent/embedded/bin/python{self.python_version[0]}'
        )

    def _format_command(self, command: list[str]) -> list[str]:
        cmd = ['docker', 'exec', self._container_name]

        if command[0] == 'pip':
            command = command[1:]
            cmd.extend([self._python_path, '-m', 'pip'])

        cmd.extend(command)
        return cmd

    def _captured_process(self, command: list[str]) -> subprocess.CompletedProcess:
        return self.platform.run_command(
            command, stdout=self.platform.modules.subprocess.PIPE, stderr=self.platform.modules.subprocess.STDOUT
        )

    def start(self, *, agent_build: str, local_packages: dict[Path, str], env_vars: dict[str, Any]) -> None:
        if not agent_build:
            agent_build = 'datadog/agent-dev:master'

        # Add a potentially missing `py` suffix for default non-RC builds
        if (
            'rc' not in agent_build
            and 'py' not in agent_build
            and agent_build != 'datadog/agent:6'
            and agent_build != 'datadog/agent:7'
        ):
            agent_build = f'{agent_build}-py{self.python_version[0]}'

        env_vars = env_vars.copy()
        if 'DD_API_KEY' not in env_vars:
            # Containerized agents require an API key and this fake key must be the proper length
            env_vars['DD_API_KEY'] = 'a' * 32

        # Set Agent hostname for CI
        env_vars['DD_HOSTNAME'] = get_hostname()

        # Run API on a random free port
        env_vars['DD_API_PORT'] = str(find_free_port(get_ip()))

        # Disable trace Agent
        env_vars['DD_APM_ENABLED'] = 'false'

        # Set up telemetry
        env_vars['DD_TELEMETRY_ENABLED'] = '1'
        env_vars['DD_EXPVAR_PORT'] = '5000'

        # TODO: Remove this when Python 2 support is removed
        #
        # Don't write .pyc, needed to fix this issue (only Python 2):
        # More info: https://github.com/DataDog/integrations-core/pull/5454
        # When reinstalling a package, .pyc are not cleaned correctly. The issue is fixed by not writing them
        # in the first place.
        env_vars['PYTHONDONTWRITEBYTECODE'] = '1'

        volumes = []

        # Mount the config directory, not the file, to ensure updates are propagated:
        # https://github.com/moby/moby/issues/15793#issuecomment-135411504
        volumes.append(f'{self.config_file.parent}:{self._config_mount_dir}')

        # It is safe to assume that the directory name is unique across all repos
        for local_package in local_packages:
            volumes.append(f'{local_package}:{self._package_mount_dir}{local_package.name}')

        if not self._is_windows_container:
            volumes.append('/proc:/host/proc')

        if not self.platform.windows:
            volumes.extend(self.metadata.get('docker_volumes', []))
        elif not self._is_windows_container:
            for volume in self.metadata.get('docker_volumes', []):
                parts = volume.split(':')
                possible_file = ':'.join(parts[:2])
                if not os.path.isfile(possible_file):
                    volumes.append(volume)
                else:
                    # Workaround for https://github.com/moby/moby/issues/30555
                    vm_file = possible_file.replace(':', '/', 1).replace('\\', '/')
                    remaining = ':'.join(parts[2:])
                    volumes.append(f'/{vm_file}:{remaining}')

        self.platform.run_command(['docker', 'pull', agent_build], check=True)

        command = [
            'docker',
            'run',
            # Keep it up
            '-d',
            # Ensure consistent naming
            '--name',
            self._container_name,
        ]

        # Ensure access to host network
        #
        # Windows containers accessing the host network must use `docker.for.win.localhost` or `host.docker.internal`:
        # https://docs.docker.com/docker-for-windows/networking/#use-cases-and-workarounds
        if not self._is_windows_container:
            command.extend(['--network', 'host'])

        for volume in volumes:
            command.extend(['-v', volume])

        # Any environment variables passed to the start command in addition to the default ones
        for key, value in sorted(env_vars.items()):
            command.extend(['-e', f'{key}={value}'])

        # The docker `--add-host` command will reliably create entries in the `/etc/hosts` file,
        # otherwise, edits to that file will be overwritten on container restarts
        for host, ip in self.metadata.get('custom_hosts', []):
            command.extend(['--add-host', f'{host}:{ip}'])

        if dogstatsd_port := env_vars.get('DD_DOGSTATSD_PORT'):
            command.extend(['-p', f'{dogstatsd_port}:{dogstatsd_port}/udp'])

        if 'proxy' in self.metadata:
            if 'http' in self.metadata['proxy']:
                command.extend(['-e', f'DD_PROXY_HTTP={self.metadata["proxy"]["http"]}'])
            if 'https' in self.metadata['proxy']:
                command.extend(['-e', f'DD_PROXY_HTTPS={self.metadata["proxy"]["https"]}'])

        # The chosen tag
        command.append(agent_build)

        process = self._captured_process(command)
        if process.returncode:
            raise RuntimeError(
                f'Unable to start Agent container `{self._container_name}`: {process.stdout.decode("utf-8")}'
            )

        post_install_commands = self.metadata.get('post_install_commands', [])
        if post_install_commands:
            for post_install_command in post_install_commands:
                formatted_command = self._format_command(self.platform.modules.shlex.split(post_install_command))
                process = self.platform.run_command(formatted_command)
                if process.returncode:
                    raise RuntimeError(
                        f'Unable to run post-install command in Agent container `{self._container_name}`: '
                        f'{process.stdout.decode("utf-8")}'
                    )

        if local_packages:
            base_pip_command = self._format_command(['pip', 'install', '--disable-pip-version-check', '-e'])
            for local_package, features in local_packages.items():
                package_mount = f'{self._package_mount_dir}{local_package.name}{features}'
                process = self.platform.run_command([*base_pip_command, package_mount])
                if process.returncode:
                    raise RuntimeError(
                        f'Unable to install package `{local_package.name}` in Agent container '
                        f'`{self._container_name}`: {process.stdout.decode("utf-8")}'
                    )

        if local_packages or post_install_commands:
            self.restart()

    def stop(self) -> None:
        for command in (
            ['docker', 'stop', '-t', '0', self._container_name],
            ['docker', 'rm', self._container_name],
        ):
            process = self._captured_process(command)
            if process.returncode:
                raise RuntimeError(
                    f'Unable to stop Agent container `{self._container_name}`: {process.stdout.decode("utf-8")}'
                )

    def restart(self) -> None:
        process = self._captured_process(['docker', 'restart', self._container_name])
        if process.returncode:
            raise RuntimeError(
                f'Unable to restart Agent container `{self._container_name}`: {process.stdout.decode("utf-8")}'
            )

    def is_running(self) -> bool:
        process = self._captured_process(['docker', 'ps', '-a', '--format', '{{.Names}}'])
        if process.returncode:
            return False

        for line in process.stdout.decode('utf-8').splitlines():
            if line == self._container_name:
                return True

        return False

    def status(self) -> None:
        self.platform.exit_with_command(['docker', 'exec', self._container_name, 'agent', 'status'])

    def logs(self) -> None:
        self.platform.exit_with_command(['docker', 'logs', self._container_name])

    def check(self, config_file: Path | None) -> None:
        self.platform.exit_with_command(
            ['docker', 'exec', self._container_name, 'agent', 'check', self.integration.name]
        )


def get_hostname():
    import socket

    return socket.gethostname()


def find_free_port(ip):
    """Return a port available for listening on the given `ip`."""
    import socket
    from contextlib import closing

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind((ip, 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def get_ip():
    """Return the IP address used to connect to external networks."""
    import socket
    from contextlib import closing

    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
        # doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        return s.getsockname()[0]
