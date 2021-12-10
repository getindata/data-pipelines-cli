import click

from .cli_commands.compile import compile_project_command
from .cli_commands.create import create_command
from .cli_commands.deploy import deploy_command
from .cli_commands.init import init_command
from .cli_commands.run import run_command
from .cli_commands.template import list_templates_command
from .cli_commands.test import test_command


@click.group()
def cli() -> None:
    pass


cli.add_command(compile_project_command)
cli.add_command(create_command)
cli.add_command(deploy_command)
cli.add_command(init_command)
cli.add_command(run_command)
cli.add_command(list_templates_command)
cli.add_command(test_command)
