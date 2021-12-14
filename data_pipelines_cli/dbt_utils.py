import pathlib
import sys
from typing import Any, Dict, Optional, Tuple

import yaml

from .cli_constants import BUILD_DIR
from .cli_utils import echo_subinfo, subprocess_run
from .config_generation import (
    generate_profiles_yml,
    read_dictionary_from_config_directory,
)
from .data_structures import DataPipelinesConfig, read_config


def _read_dbt_vars_from_configs(dbt_env_config: Dict[str, Any]) -> str:
    dp_config = read_config() or DataPipelinesConfig(templates={}, vars={})
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
            env,
            "--vars",
            dbt_vars,
        ]
    )
