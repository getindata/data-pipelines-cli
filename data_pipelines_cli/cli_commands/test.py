import click

from ..config_generation import get_profiles_yml_build_path
from ..dbt_utils import run_dbt_command
from .compile import compile_project


def test(env: str) -> None:
    """
    Run tests of the project on the local machine

    :param env: Name of the environment
    :type env: str
    """
    compile_project(env)
    profiles_path = get_profiles_yml_build_path(env)
    run_dbt_command(("test",), env, profiles_path)


@click.command(name="test", help="Run tests of the project on the local machine")
@click.option(
    "--env",
    default="local",
    type=str,
    show_default=True,
    help="Name of the environment",
)
def test_command(env: str) -> None:
    test(env)
