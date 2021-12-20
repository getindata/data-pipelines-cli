import click

from ..dbt_utils import run_dbt_command


def run(env: str) -> None:
    """
    Run the project on the local machine

    :param env: Name of the environment
    :type env: str
    """
    run_dbt_command(("run",), env, None)


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
