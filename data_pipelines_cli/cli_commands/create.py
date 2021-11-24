import sys

import click
import copier
import questionary

from data_pipelines_cli.cli_utils import echo_error
from data_pipelines_cli.data_structures import read_config_or_exit


def create(project_path: str) -> None:
    config = read_config_or_exit()
    if len(config["templates"]) == 0:
        echo_error(
            "No template provided. Run 'dp template new' to define one.",
        )
        sys.exit(1)

    template_name = questionary.select(
        "", choices=list(config["templates"].keys())
    ).ask()
    template_config = config["templates"][template_name]
    copier.copy(src_path=template_config["template_path"], dst_path=project_path)


@click.command(name="create")
@click.argument(
    "project_path",
    type=click.Path(writable=True, path_type=str, dir_okay=True, file_okay=False),
)
def create_command(project_path: str) -> None:
    create(project_path)
