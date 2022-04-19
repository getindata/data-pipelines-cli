import click

from ..config_generation import get_profiles_dir_build_path
from ..dbt_utils import run_dbt_command
from .compile import compile_project


def docs(env: str, port: int) -> None:
    """
    Generate and serve dbt documentation.

    :param env: Name of the environment
    :type env: str
    :param port: Port to serve dbt documentation on.
    :type port: int
    """
    compile_project(env)
    profiles_path = get_profiles_dir_build_path(env)
    run_dbt_command(("docs", "serve", "--port", str(port)), env, profiles_path)


@click.command(name="docs-serve", help="Generate and serve dbt documentation.")
@click.option(
    "--env",
    default="local",
    type=str,
    show_default=True,
    help="Name of the environment",
)
@click.option(
    "--port",
    default=9328,
    type=int,
    show_default=True,
    help="Port to be used by the 'dbt docs serve' command",
)
def docs_command(env: str, port: int) -> None:
    docs(env, port)
