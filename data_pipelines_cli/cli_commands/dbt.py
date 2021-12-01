import subprocess
from typing import Tuple

import click


def dbt(command: Tuple[str, ...], target: str) -> None:
    subprocess.run(["dbt", *command, "--profiles-dir", ".", "--target", target])


@click.command(name="dbt")
@click.argument("command", nargs=-1)
@click.option("-t", "--target", default="local", type=str)
def dbt_command(command: Tuple[str, ...], target: str) -> None:
    dbt(command, target)
