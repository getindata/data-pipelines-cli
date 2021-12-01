import sys

import click
import questionary
import yaml

from data_pipelines_cli.cli_constants import CONFIGURATION_PATH
from data_pipelines_cli.data_structures import read_config_or_exit


def new_template() -> None:
    config = read_config_or_exit()
    template_name = questionary.text(
        "Name of your project template", validate=lambda text: len(text) > 0
    ).ask()
    if config["templates"].get(template_name):
        overwrite_confirm = questionary.confirm(
            f"Project template named {template_name} already exists. "
            f"Do you want to overwrite it?",
            default=False,
        ).ask()
        if not overwrite_confirm:
            sys.exit(1)
    template_path: str = questionary.text(
        "Template path (repository address)",
        validate=lambda text: len(text) > 0,
    ).ask()

    config["templates"][template_name] = {
        "template_name": template_name,
        "template_path": template_path,
    }

    with open(CONFIGURATION_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def list_templates() -> None:
    config = read_config_or_exit()

    click.echo("AVAILABLE TEMPLATES:\n")
    for tc in config["templates"].values():
        click.echo(yaml.dump(tc))


@click.group(name="template")
def template_group() -> None:
    pass


@template_group.command(name="new")
def new_template_command() -> None:
    new_template()


@template_group.command(name="list")
def list_templates_command() -> None:
    list_templates()
