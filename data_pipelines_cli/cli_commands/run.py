import click

from ..dbt_utils import run_dbt_command


def run(env: str) -> None:
    run_dbt_command(("run",), env, None)


@click.command(name="run")
@click.option("--env", default="local", type=str)
def run_command(env: str) -> None:
    run(env)
