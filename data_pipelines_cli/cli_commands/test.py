import click

from ..dbt_utils import run_dbt_command


def test(env: str) -> None:
    run_dbt_command(("test",), env, None)


@click.command(name="test")
@click.option("--env", default="local", type=str)
def test_command(env: str) -> None:
    test(env)
