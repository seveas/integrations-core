# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Generator

from ddev.e2e.constants import E2EEnvVars
from ddev.utils.structures import EnvVars


class E2EEnvironmentRunner:
    def __init__(self, env: str):
        self.__env = env

    @contextmanager
    def start(self) -> Generator[list[str], None, None]:
        with EnvVars({E2EEnvVars.TEAR_DOWN: 'false'}):
            yield self.base_command()

    @contextmanager
    def stop(self) -> Generator[list[str], None, None]:
        with EnvVars({E2EEnvVars.SET_UP: 'false'}):
            yield self.base_command()

    def base_command(self) -> list[str]:
        return [
            sys.executable,
            '-m',
            'hatch',
            'env',
            'run',
            '--env',
            self.__env,
            '--',
            'test',
            '--capture=no',
            '--disable-warnings',
            '--no-header',
            '--no-summary',
            '--exitfirst',
            # We need -2 verbosity and by default the test command sets the verbosity to +2
            '-qqqq',
        ]
