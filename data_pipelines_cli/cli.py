import getpass
import pathlib
import shutil
import subprocess
import sys
from typing import Dict

import click
import copier
import questionary
import yaml

if sys.version_info >= (3, 8):
    from typing import TypedDict  # pylint: disable=no-name-in-module
else:
    from typing_extensions import TypedDict


CONFIGURATION_PATH: pathlib.Path = pathlib.Path.home().joinpath(".dp.yml")


class TemplateConfig(TypedDict):
    template_name: str
    template_path: str


class DataPipelinesConfig(TypedDict):
    username: str
    templates: Dict[str, TemplateConfig]


@click.group()
def cli() -> None:
    pass


@cli.command()
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


def read_config_or_exit() -> DataPipelinesConfig:
    if not CONFIGURATION_PATH.is_file():
        click.secho(
            "No configuration file found. Run 'dp init' to create it.",
            fg="red",
        )
        sys.exit(1)

    with open(CONFIGURATION_PATH, "r") as f:
        return yaml.safe_load(f)


@cli.group()
def template() -> None:
    pass


@template.command(name="new")
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


@template.command(name="list")
def list_templates() -> None:
    config = read_config_or_exit()

    click.echo("AVAILABLE TEMPLATES:\n")
    for tc in config["templates"].values():
        click.echo(yaml.dump(tc))


@cli.command()
@click.argument(
    "project_path",
    type=click.Path(
        writable=True, path_type=str, dir_okay=True, file_okay=False
    ),
)
def create(project_path: str) -> None:
    config = read_config_or_exit()
    if len(config["templates"]) == 0:
        click.secho(
            "No template provided. Run 'dp template new' to define one.",
            fg="red",
        )
        sys.exit(1)

    template_name = questionary.select(
        "", choices=list(config["templates"].keys())
    ).ask()
    template_config = config["templates"][template_name]
    copier.copy(
        src_path=template_config["template_path"], dst_path=project_path
    )


@cli.command()
@click.argument("command")
@click.option("-t", "--target", default="local", type=str)
def dbt(command: str, target: str) -> None:
    if not shutil.which("dbt"):
        click.secho(
            "dbt not found. Install dbt "
            "[https://docs.getdbt.com/dbt-cli/installation] "
            "and rerun the command",
            fg="red",
        )
        sys.exit(1)

    subprocess.run(["dbt", command, "--profiles-dir", ".", "--target", target])
