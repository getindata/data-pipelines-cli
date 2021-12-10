import pathlib
import sys
import tempfile
from typing import Optional, Sequence

import click
import copier
import questionary
import yaml

from ..cli_constants import CONFIGURATION_PATH, DEFAULT_GLOBAL_CONFIG
from ..data_structures import DataPipelinesConfig


def _download_global_config(config_path: str) -> DataPipelinesConfig:
    with tempfile.TemporaryDirectory() as tmp:
        copier.copy(config_path, tmp, quiet=True)
        with open(pathlib.Path(tmp).joinpath("dp.yml")) as config_file:
            config = yaml.safe_load(config_file)
    return config


def init(config_path: Optional[str]) -> None:
    if CONFIGURATION_PATH.is_file():
        overwrite_confirm = questionary.confirm(
            "dp config already exists. Do you want to overwrite it?",
            default=False,
        ).ask()
        if not overwrite_confirm:
            sys.exit(1)

    if config_path:
        config = _download_global_config(config_path)
    else:
        config = DEFAULT_GLOBAL_CONFIG

    with open(CONFIGURATION_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


@click.command(name="init")
@click.argument("config_path", nargs=-1)
def init_command(config_path: Sequence[str]) -> None:
    init(config_path[0] if config_path else None)
