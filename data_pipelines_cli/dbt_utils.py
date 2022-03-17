from __future__ import annotations

import pathlib
import subprocess
import sys
from typing import Any, Dict, Tuple

import yaml

from .cli_constants import BUILD_DIR, get_dbt_profiles_env_name
from .cli_utils import echo_subinfo, subprocess_run
from .config_generation import read_dictionary_from_config_directory
from .data_structures import DataPipelinesConfig, read_env_config
from .errors import NoConfigFileError


def read_dbt_vars_from_configs(env: str) -> Dict[str, Any]:
    """Read `vars` field from dp configuration file (``$HOME/.dp.yml``), base
    ``dbt.yml`` config (``config/base/dbt.yml``) and environment-specific config
    (``config/{env}/dbt.yml``) and compile into one dictionary.

    :param env: Name of the environment
    :type env: str
    :return: Dictionary with `vars` and their keys
    :rtype: Dict[str, Any]
    """
    dbt_env_config = read_dictionary_from_config_directory(
        BUILD_DIR.joinpath("dag"), env, "dbt.yml"
    )

    try:
        dp_config = read_env_config()
    except NoConfigFileError:
        dp_config = DataPipelinesConfig(templates={}, vars={})
    dp_vars = dp_config.get("vars", {})
    dbt_vars: Dict[str, str] = dbt_env_config.get("vars", {})

    return dict(dbt_vars, **dp_vars)


def _dump_dbt_vars_from_configs_to_string(env: str) -> str:
    dbt_vars = read_dbt_vars_from_configs(env)
    return yaml.dump(dbt_vars, default_flow_style=True, width=sys.maxsize)


def run_dbt_command(
    command: Tuple[str, ...],
    env: str,
    profiles_path: pathlib.Path,
    log_format_json: bool = False,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    """
    Run dbt subprocess in a context of specified *env*.

    :param command: Tuple representing dbt command and its optional arguments
    :type command: Tuple[str, ...]
    :param env: Name of the environment
    :type env: str
    :param profiles_path: Path to the directory containing `profiles.yml` file
    :type profiles_path: pathlib.Path
    :param log_format_json: Whether to run dbt command with `--log-format=json` flag
    :type log_format_json: bool
    :param capture_output: Whether to capture stdout of subprocess.
    :type capture_output: bool
    :return: State of the completed process
    :rtype: subprocess.CompletedProcess[bytes]
    :raises SubprocessNotFound: dbt not installed
    :raises SubprocessNonZeroExitError: dbt exited with error
    """
    command_str = " ".join(list(command))
    echo_subinfo(f"dbt {command_str}")

    dbt_env_config = read_dictionary_from_config_directory(
        BUILD_DIR.joinpath("dag"), env, "dbt.yml"
    )
    dbt_vars = _dump_dbt_vars_from_configs_to_string(env)
    return subprocess_run(
        [
            "dbt",
            *(["--log-format=json"] if log_format_json else []),
            *command,
            "--profile",
            dbt_env_config["target_type"],
            "--profiles-dir",
            str(profiles_path),
            "--target",
            get_dbt_profiles_env_name(env),
            "--vars",
            dbt_vars,
        ],
        capture_output=capture_output,
    )
