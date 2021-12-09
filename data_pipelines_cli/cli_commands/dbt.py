import subprocess
from typing import Tuple

import click

from data_pipelines_cli.cli_utils import echo_subinfo


def dbt(command: Tuple[str, ...], target: str) -> None:
    command_str = " ".join(list(command))
    echo_subinfo(f"dbt {command_str}")
    subprocess.run(["dbt", *command, "--profiles-dir", ".", "--target", target])


@click.command(name="dbt")
@click.argument("command", nargs=-1)
@click.option("-t", "--target", default="local", type=str)
def dbt_command(command: Tuple[str, ...], target: str) -> None:
    dbt(command, target)
