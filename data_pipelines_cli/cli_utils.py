from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, List, Optional

import click

from data_pipelines_cli.errors import (
    DataPipelinesError,
    SubprocessNonZeroExitError,
    SubprocessNotFound,
)


def echo_error(text: str, **kwargs: Any) -> None:
    """
    Print an error message to stderr using click-specific print function.

    :param text: Message to print
    :type text: str
    :param kwargs:
    """
    click.secho(text, file=sys.stderr, fg="red", **kwargs)


def echo_warning(text: str, **kwargs: Any) -> None:
    """
    Print a warning message to stderr using click-specific print function.

    :param text: Message to print
    :type text: str
    :param kwargs:
    """
    click.secho(text, file=sys.stderr, fg="yellow", **kwargs)


def echo_info(text: str, **kwargs: Any) -> None:
    """
    Print a message to stdout using click-specific print function.

    :param text: Message to print
    :type text: str
    :param kwargs:
    """
    click.secho(text, fg="blue", bold=True, **kwargs)


def echo_subinfo(text: str, **kwargs: Any) -> None:
    """
    Print a subinfo message to stdout using click-specific print function.

    :param text: Message to print
    :type text: str
    :param kwargs:
    """
    click.secho(text, fg="bright_blue", **kwargs)


def get_argument_or_environment_variable(
    argument: Optional[str], argument_name: str, environment_variable_name: str
) -> str:
    """
    Given *argument* is not ``None``, returns its value. Otherwise, searches
    for *environment_variable_name* amongst environment variables and returns
    it. If such a variable is not set, raises :exc:`.DataPipelinesError`.

    :param argument: Optional value passed to the CLI as the *argument_name*
    :type argument: Optional[str]
    :param argument_name: Name of the CLI's argument
    :type argument_name: str
    :param environment_variable_name: Name of the environment variable to search for
    :type environment_variable_name: str
    :return: Value of the *argument* or specified environment variable
    :raises DataPipelinesError: *argument* is ``None`` and \
        *environment_variable_name* is not set
    """
    result = argument or os.environ.get(environment_variable_name)
    if not result:
        raise DataPipelinesError(
            f"Could not get {environment_variable_name}. Either set it as an "
            f"environment variable {environment_variable_name} or pass as a "
            f"`--{argument_name}` CLI argument."
        )
    return result


def subprocess_run(args: List[str]) -> subprocess.CompletedProcess[bytes]:
    """
    Runs subprocess and returns its state if completed with a success. If not,
    raises :exc:`.SubprocessNonZeroExitError`.

    :param args: List of strings representing subprocess and its arguments
    :type args: List[str]
    :return: State of the completed process
    :rtype: subprocess.CompletedProcess[bytes]
    :raises SubprocessNonZeroExitError: subprocess exited with non-zero exit code
    """
    try:
        return subprocess.run(args, check=True)
    except FileNotFoundError:
        raise SubprocessNotFound(args[0])
    except subprocess.CalledProcessError as err:
        raise SubprocessNonZeroExitError(args[0], err.returncode)
