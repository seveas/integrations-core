# (C) Datadog, Inc. 2023-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ddev.utils.fs import Path


class EnvData:
    def __init__(self, storage_dir: Path):
        self.__storage_dir = storage_dir

    @property
    def storage_dir(self) -> Path:
        return self.__storage_dir

    @property
    def metadata_file(self) -> Path:
        return self.storage_dir / 'metadata.json'

    @property
    def config_dir(self) -> Path:
        return self.storage_dir / 'config'

    @property
    def config_file(self) -> Path:
        return self.config_dir / f'{self.storage_dir.parent.name}.yaml'

    def read_config(self) -> dict[str, Any]:
        import yaml

        return yaml.safe_load(self.config_file.read_text())

    def write_config(self, config: dict[str, Any]) -> None:
        import yaml

        if 'instances' not in config:
            config = {'instances': [config]}

        self.config_file.parent.ensure_dir_exists()
        self.config_file.write_text(yaml.safe_dump(config, default_flow_style=False))

    def read_metadata(self) -> dict[str, Any]:
        import json

        return json.loads(self.metadata_file.read_text())

    def write_metadata(self, metadata: dict[str, Any]) -> None:
        import json

        self.metadata_file.parent.ensure_dir_exists()
        self.metadata_file.write_text(json.dumps(metadata, indent=2))

    def exists(self) -> bool:
        return self.storage_dir.is_dir()

    def remove(self) -> None:
        self.storage_dir.remove()


class EnvDataStorage:
    def __init__(self, data_dir: Path):
        self.__dir = data_dir / 'env'

    def get(self, integration: str, env: str) -> EnvData:
        return EnvData(self.__dir / integration / env)
