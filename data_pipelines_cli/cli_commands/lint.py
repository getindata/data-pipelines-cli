import pathlib
import tempfile
from configparser import ConfigParser
from typing import List

import click
import yaml

from ..cli_constants import BUILD_DIR
from ..cli_utils import echo_info, echo_subinfo, echo_warning, subprocess_run
from ..config_generation import (
    generate_profiles_yml,
    read_dictionary_from_config_directory,
)
from ..errors import SQLLintError, SubprocessNonZeroExitError

SQLFLUFF_FIX_NOT_EVERYTHING_ERROR = 1
SQLFLUFF_LINT_ERROR = 65  # according to `sqlfluff.core.linter.LintingResult.stats`
SQLFLUFF_DIALECT_LOADING_ERROR = 66  # according to `sqlfluff.cli.commands.get_config`


def _get_dialect_or_default() -> str:
    """Read ``dbt.yml`` config file and return its ``target_type`` or just the ``ansi``."""
    env, dbt_filename = "base", "dbt.yml"
    dbt_env_config = read_dictionary_from_config_directory(
        BUILD_DIR.joinpath("dag"), env, dbt_filename
    ) or read_dictionary_from_config_directory(pathlib.Path.cwd(), env, dbt_filename)
    try:
        dialect = dbt_env_config["target_type"]
        echo_subinfo(f'Found target_type "{dialect}", attempting to use it as the SQL dialect.')
    except KeyError:
        dialect = "ansi"
        echo_warning(
            'Could not find `target_type` in `dbt.yml`. Using the default SQL dialect ("ansi").'
        )
    return dialect


def _get_source_tests_paths() -> List[pathlib.Path]:
    with open(pathlib.Path.cwd().joinpath("dbt_project.yml"), "r") as f:
        dbt_project_config = yaml.safe_load(f)
    dir_names: List[str] = (
        dbt_project_config.get("source-paths", [])
        + dbt_project_config.get("model-paths", [])
        + dbt_project_config.get("test-paths", [])
    )
    return list(map(lambda dir_name: pathlib.Path.cwd().joinpath(dir_name), dir_names))


def _create_temporary_sqlfluff_config(env: str) -> ConfigParser:
    config = ConfigParser()
    config["sqlfluff"] = {"templater": "dbt"}
    config["sqlfluff:templater:dbt"] = {
        "profiles_dir": str(generate_profiles_yml(env, copy_config_dir=True).absolute())
    }
    return config


def _run_sqlfluff(command: str, dialect: str, env: str, additional_args: List[str]) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_config_path = pathlib.Path(tmp_dir).joinpath("sqlfluff.config")
        with open(tmp_config_path, "w") as tmp_config:
            _create_temporary_sqlfluff_config(env).write(tmp_config)

        def sqlfluff_args(sql_dialect: str) -> List[str]:
            return [
                "sqlfluff",
                command,
                "--dialect",
                sql_dialect,
                "--config",
                str(tmp_config_path),
                *additional_args,
                *map(str, _get_source_tests_paths()),
            ]

        try:
            subprocess_run(sqlfluff_args(dialect))
        except SubprocessNonZeroExitError as err:
            if err.exit_code == SQLFLUFF_DIALECT_LOADING_ERROR and dialect != "ansi":
                subprocess_run(sqlfluff_args("ansi"))
            else:
                raise err


def _run_fix_sqlfluff(dialect: str, env: str) -> None:
    try:
        echo_subinfo("Attempting to fix SQLs. Not every error can be automatically fixed.")
        _run_sqlfluff("fix", dialect, env, ["--force"])
    except SubprocessNonZeroExitError as err:
        if err.exit_code != SQLFLUFF_FIX_NOT_EVERYTHING_ERROR:
            raise err


def _run_lint_sqlfluff(dialect: str, env: str) -> None:
    try:
        echo_subinfo("Linting SQLs.")
        _run_sqlfluff("lint", dialect, env, [])
    except SubprocessNonZeroExitError as err:
        if err.exit_code == SQLFLUFF_LINT_ERROR:
            raise SQLLintError
        else:
            raise err


def lint(fix: bool, env: str) -> None:
    """
    Lint and format SQL.

    :param fix: Whether to lint and fix linting errors, or just lint.
    :type fix: bool
    :param env: Name of the environment
    :type env: str
    """
    echo_info("Linting SQLs:")
    dialect = _get_dialect_or_default()
    if fix:
        _run_fix_sqlfluff(dialect, env)
    _run_lint_sqlfluff(dialect, env)


@click.command(
    name="lint",
    short_help="Lint and format SQL",
    help="Lint and format SQL using SQLFluff.\n\n"
    "For more information on rules and the workings of SQLFluff, "
    "refer to https://docs.sqlfluff.com/",
)
@click.option(
    "--no-fix",
    is_flag=True,
    default=False,
    type=bool,
    help="Whether to lint and fix linting errors, or just lint.",
)
@click.option(
    "--env",
    default="local",
    type=str,
    show_default=True,
    help="Name of the environment",
)
def lint_command(no_fix: bool, env: str) -> None:
    lint(not no_fix, env)
