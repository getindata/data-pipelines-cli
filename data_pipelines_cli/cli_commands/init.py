import pathlib
import tempfile
from typing import Optional, Sequence

import click
import copier
import questionary
import yaml

from ..cli_constants import CONFIGURATION_PATH, DEFAULT_GLOBAL_CONFIG
from ..data_structures import DataPipelinesConfig
from ..errors import DataPipelinesError
from ..vcs_utils import add_suffix_to_git_template_path


def _download_global_config(config_path: str) -> DataPipelinesConfig:
    config_path = add_suffix_to_git_template_path(config_path)

    with tempfile.TemporaryDirectory() as tmp:
        copier.copy(config_path, tmp, quiet=True)
        with open(pathlib.Path(tmp).joinpath("dp.yml")) as config_file:
            config = yaml.safe_load(config_file)
    return config


def init(config_path: Optional[str]) -> None:
    """
    Configure the tool for the first time.

    :param config_path: URI of the repository with a template of the config file
    :type config_path: Optional[str]
    :raises DataPipelinesError: user do not want to overwrite existing config file
    """
    if CONFIGURATION_PATH.is_file():
        overwrite_confirm = questionary.confirm(
            "dp config already exists. Do you want to overwrite it?",
            default=False,
        ).ask()
        if not overwrite_confirm:
            raise DataPipelinesError("Could not overwrite existing config")

    if config_path:
        config = _download_global_config(config_path)
    else:
        config = DEFAULT_GLOBAL_CONFIG

    with open(CONFIGURATION_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


@click.command(name="init", help="Configure the tool for the first time")
@click.argument("config_path", nargs=-1)
def init_command(config_path: Sequence[str]) -> None:
    init(config_path[0] if config_path else None)
