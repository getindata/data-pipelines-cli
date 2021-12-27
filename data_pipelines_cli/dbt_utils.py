import pathlib
import sys
from typing import Any, Dict, Tuple

import yaml

from .cli_constants import BUILD_DIR, get_dbt_profiles_env_name
from .cli_utils import echo_subinfo, subprocess_run
from .config_generation import read_dictionary_from_config_directory
from .data_structures import DataPipelinesConfig, read_config
from .errors import NoConfigFileError


def _read_dbt_vars_from_configs(dbt_env_config: Dict[str, Any]) -> str:
    try:
        dp_config = read_config()
    except NoConfigFileError:
        dp_config = DataPipelinesConfig(templates={}, vars={})
    dp_vars = dp_config.get("vars", {})
    dbt_vars: Dict[str, str] = dbt_env_config.get("vars", {})
    return yaml.dump(
        dict(dp_vars, **dbt_vars), default_flow_style=True, width=sys.maxsize
    )


def run_dbt_command(
    command: Tuple[str, ...], env: str, profiles_path: pathlib.Path
) -> None:
    """
    Runs dbt subprocess in a context of specified *env*

    :param command: Tuple representing dbt command and its optional arguments
    :type command: Tuple[str, ...]
    :param env: Name of the environment
    :type env: str
    :param profiles_path: Path to the directory containing `profiles.yml` file
    :type profiles_path: pathlib.Path
    :raises SubprocessNotFound: dbt not installed
    :raises SubprocessNonZeroExitError: dbt exited with error
    """
    command_str = " ".join(list(command))
    echo_subinfo(f"dbt {command_str}")

    dbt_env_config = read_dictionary_from_config_directory(
        BUILD_DIR.joinpath("dag"), env, "dbt.yml"
    )
    dbt_vars = _read_dbt_vars_from_configs(dbt_env_config)
    subprocess_run(
        [
            "dbt",
            *command,
            "--profile",
            dbt_env_config["target_type"],
            "--profiles-dir",
            str(profiles_path),
            "--target",
            get_dbt_profiles_env_name(env),
            "--vars",
            dbt_vars,
        ]
    )
