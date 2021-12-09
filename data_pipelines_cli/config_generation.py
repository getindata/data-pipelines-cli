import pathlib
import sys
from typing import Any, Dict

import yaml
from dbt_airflow_manifest_parser.config_utils import read_config

from .cli_constants import BUILD_DIR, profiles_build_path
from .cli_utils import echo_info, echo_subinfo

if sys.version_info >= (3, 8):
    from typing import TypedDict  # pylint: disable=no-name-in-module
else:
    from typing_extensions import TypedDict


class DbtProfile(TypedDict):
    target: str
    outputs: Dict[str, Dict[str, Any]]


def _generate_profile_dict(env: str) -> Dict[str, DbtProfile]:
    dbt_env_config = read_config(BUILD_DIR.joinpath("dag"), env, "dbt.yml")
    dbt_target: str = dbt_env_config["target"]
    dbt_target_type: str = dbt_env_config["target_type"]
    target_type_config = read_config(
        BUILD_DIR.joinpath("dag"), env, f"{dbt_target_type}.yml"
    )
    target_type_config["type"] = dbt_target_type

    return {
        dbt_target_type: {
            "target": dbt_target,
            "outputs": {dbt_target: target_type_config},
        }
    }


def generate_profiles_yml(env: str) -> pathlib.Path:
    echo_info("Generating .profiles.yml")
    profile = _generate_profile_dict(env)
    profiles_path = profiles_build_path(env)

    profiles_path.parent.mkdir(parents=True, exist_ok=True)
    with open(profiles_path, "w") as profiles:
        yaml.dump(profile, profiles, default_flow_style=False)

    echo_subinfo(f"Generated .profiles.yml in {profiles_path}")

    return profiles_path
