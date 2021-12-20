from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, List, Optional

import click


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
    argument: Optional[str], environment_variable_name: str
) -> Optional[str]:
    """
    Given *argument* is not `None`, returns its value. Otherwise, searches
    for *environment_variable_name* amongst environment variables and returns
    it.

    :param argument: Optional value passed to the CLI as the *argument_name*
    :type argument: Optional[str]
    :param environment_variable_name: Name of the environment variable to search for
    :type environment_variable_name: str
    :return: Value of the *argument* or specified environment variable
    """
    return argument or os.environ.get(environment_variable_name)


def get_argument_or_environment_variable_or_exit(
    argument: Optional[str], argument_name: str, environment_variable_name: str
) -> str:
    """
    Given *argument* is not `None`, returns its value. Otherwise, searches
    for *environment_variable_name* amongst environment variables and returns
    it. If such a variable is not set, exits program with system exit status
    set to 1.

    :param argument: Optional value passed to the CLI as the *argument_name*
    :type argument: Optional[str]
    :param argument_name: Name of the CLI's argument
    :type argument_name: str
    :param environment_variable_name: Name of the environment variable to search for
    :type environment_variable_name: str
    :return: Value of the *argument* or specified environment variable
    """
    result = get_argument_or_environment_variable(argument, environment_variable_name)
    if not result:
        echo_error(
            f"Could not get {environment_variable_name}. Either set it as an "
            f"environment variable {environment_variable_name} or pass as a "
            f"`--{argument_name}` CLI argument"
        )
        sys.exit(1)
    return result


def subprocess_run(args: List[str]) -> subprocess.CompletedProcess[bytes]:
    """
    Runs subprocess and returns its state if completed with a success. If not,
    exits the program with system exit status set to 1.

    :param args: List of strings representing subprocess and its arguments
    :type args: List[str]
    :return: State of the completed process
    :rtype: subprocess.CompletedProcess[bytes]
    """
    try:
        return subprocess.run(args, check=True)
    except subprocess.CalledProcessError as err:
        echo_error(f"{args[0]} has exited with non-zero exit code: {err.returncode}")
        sys.exit(1)
