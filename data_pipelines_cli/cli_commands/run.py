import click

from ..config_generation import generate_profiles_yml
from ..dbt_utils import run_dbt_command


def run(env: str) -> None:
    """
    Run the project on the local machine

    :param env: Name of the environment
    :type env: str
    """
    profiles_path = generate_profiles_yml(env)
    run_dbt_command(("deps",), env, profiles_path)
    run_dbt_command(("run",), env, profiles_path)


@click.command(name="run", help="Run the project on the local machine")
@click.option(
    "--env",
    default="local",
    type=str,
    show_default=True,
    help="Name of the environment",
)
def run_command(env: str) -> None:
    run(env)
