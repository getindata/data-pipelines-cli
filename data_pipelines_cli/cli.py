import sys

import click

from .cli_commands.clean import clean_command
from .cli_commands.compile import compile_project_command
from .cli_commands.create import create_command
from .cli_commands.deploy import deploy_command
from .cli_commands.init import init_command
from .cli_commands.prepare_env import prepare_env_command
from .cli_commands.run import run_command
from .cli_commands.template import list_templates_command
from .cli_commands.test import test_command
from .cli_utils import echo_error
from .errors import DataPipelinesError


@click.group()
@click.version_option(prog_name="dp")
def _cli() -> None:
    pass


def cli() -> None:
    try:
        _cli()
    except DataPipelinesError as err:
        echo_error(f"CLI Error: {err.message}")
        sys.exit(1)


_cli.add_command(clean_command)
_cli.add_command(compile_project_command)
_cli.add_command(create_command)
_cli.add_command(deploy_command)
_cli.add_command(init_command)
_cli.add_command(prepare_env_command)
_cli.add_command(run_command)
_cli.add_command(list_templates_command)
_cli.add_command(test_command)
