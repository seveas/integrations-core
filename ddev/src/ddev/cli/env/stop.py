# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ddev.cli.application import Application


@click.command(short_help='Stop an environment')
@click.argument('intg_name')
@click.argument('environment')
@click.pass_obj
def stop(app: Application, *, intg_name: str, environment: str):
    """
    Stop an environment.
    """
    from ddev.e2e.agent import get_agent_interface
    from ddev.e2e.config import EnvDataStorage
    from ddev.e2e.constants import E2EEnvVars
    from ddev.e2e.run import E2EEnvironmentRunner
    from ddev.utils.fs import temp_directory

    integration = app.repo.integrations.get(intg_name)
    env_data = EnvDataStorage(app.data_dir).get(integration.name, environment)
    runner = E2EEnvironmentRunner(environment)

    if not env_data.exists():
        app.abort(f'Environment `{environment}` for integration `{integration.name}` is not running')

    app.display_header(f'Stopping: {environment}')

    # TODO: remove this required result file indicator once the E2E migration is complete
    with temp_directory() as temp_dir:
        result_file = temp_dir / 'result.json'
        env_vars = {E2EEnvVars.RESULT_FILE: str(result_file)}

        metadata = env_data.read_metadata()
        env_vars.update(metadata['env_vars'])

        agent_type = metadata['env_type']
        agent = get_agent_interface(agent_type)(app.platform, integration, environment, metadata, env_data.config_file)

        try:
            agent.stop()
        finally:
            env_data.remove()

            with integration.path.as_cwd(env_vars=env_vars), runner.stop() as command:
                process = app.platform.run_command(command)
                if process.returncode:
                    app.abort(code=process.returncode)
