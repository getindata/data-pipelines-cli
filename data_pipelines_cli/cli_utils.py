import os
import sys
from typing import Optional

import click


def echo_error(text: str, **kwargs):
    click.secho(text, file=sys.stderr, fg="red", **kwargs)


def echo_info(text: str, **kwargs):
    click.secho(text, fg="blue", bold=True, **kwargs)


def echo_subinfo(text: str, **kwargs):
    click.secho(text, fg="bright_blue", **kwargs)


def get_argument_or_environment_variable(
    argument: Optional[str], argument_name: str, environment_variable_name: str
) -> str:
    result = argument or os.environ.get(environment_variable_name)
    if not result:
        echo_error(
            f"Could not get {environment_variable_name}. Either set it as an "
            f"environment variable {environment_variable_name} or pass as a "
            f"`--{argument_name}` CLI argument"
        )
        sys.exit(1)
    return result
