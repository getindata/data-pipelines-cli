import click

from ..dbt_utils import run_dbt_command


def test(env: str) -> None:
    """
    Run tests of the project on the local machine

    :param env: Name of the environment
    :type env: str
    """
    run_dbt_command(("test",), env, None)


@click.command(name="test", help="Run tests of the project on the local machine")
@click.option("--env", default="local", type=str, help="Name of the environment")
def test_command(env: str) -> None:
    test(env)
