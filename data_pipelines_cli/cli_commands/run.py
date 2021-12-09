import click

from .compile import dbt


def run(env: str) -> None:
    dbt(("run",), env, None)


@click.command(name="run")
@click.option("--env", default="local", type=str)
def run_command(env: str) -> None:
    run(env)
