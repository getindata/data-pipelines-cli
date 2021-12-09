import click

from .compile import dbt


def test(env: str) -> None:
    dbt(("test",), env, None)


@click.command(name="test")
@click.option("--env", default="local", type=str)
def test_command(env: str) -> None:
    test(env)
