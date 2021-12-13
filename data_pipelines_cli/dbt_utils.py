import pathlib
import sys
from typing import Any, Dict, Optional, Tuple

import dbt_airflow_manifest_parser.config_utils as dbt_airflow_manifest_parser
import yaml

from .cli_constants import BUILD_DIR
from .cli_utils import echo_subinfo, subprocess_run
from .config_generation import generate_profiles_yml
from .data_structures import read_config_or_exit


def _read_dbt_vars_from_configs(dbt_env_config: Dict[str, Any]) -> str:
    dp_config = read_config_or_exit()
    dp_vars = dp_config.get("vars", {})
    dbt_vars: Dict[str, str] = dbt_env_config.get("vars", {})
    return yaml.dump(
        dict(dp_vars, **dbt_vars), default_flow_style=True, width=sys.maxsize
    )


def run_dbt_command(
    command: Tuple[str, ...], env: str, profiles_path: Optional[pathlib.Path]
) -> None:
    command_str = " ".join(list(command))
    echo_subinfo(f"dbt {command_str}")

    profiles_path = profiles_path or generate_profiles_yml(env)
    dbt_env_config = dbt_airflow_manifest_parser.read_config(
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
            env,
            "--vars",
            dbt_vars,
        ]
    )
