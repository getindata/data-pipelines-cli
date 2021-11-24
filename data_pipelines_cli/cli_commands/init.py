import getpass
import sys

import click
import questionary
import yaml

from data_pipelines_cli.cli_constants import CONFIGURATION_PATH
from data_pipelines_cli.data_structures import DataPipelinesConfig


def init() -> None:
    if CONFIGURATION_PATH.is_file():
        overwrite_confirm = questionary.confirm(
            "dp config already exists. Do you want to overwrite it?",
            default=False,
        ).ask()
        if not overwrite_confirm:
            sys.exit(1)

    username: str = questionary.text(
        "What's your username?",
        default=getpass.getuser(),
        validate=lambda text: len(text) > 0,
    ).ask()

    config: DataPipelinesConfig = {
        "username": username,
        "templates": {},
    }
    with open(CONFIGURATION_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


@click.command(name="init")
def init_command() -> None:
    init()
