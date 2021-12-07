import pathlib
import shutil
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


def _copy_src_dir_to_dst_dir(src_dir: pathlib.Path, dst_dir: pathlib.Path) -> None:
    # It has to be deleted before copying, as `copytree` complains with
    # `FileExistsError`
    if pathlib.Path.exists(dst_dir):
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)


def copy_dag_dir_to_build_dir() -> None:
    dag_src_path = pathlib.Path.cwd().joinpath("dag")
    dag_dst_path = BUILD_DIR.joinpath("dag")
    _copy_src_dir_to_dst_dir(dag_src_path, dag_dst_path)


def copy_config_dir_to_build_dir() -> None:
    config_src_path = pathlib.Path.cwd().joinpath("config")
    dag_dst_path = BUILD_DIR.joinpath("dag", "config")
    echo_info(f"Copying 'config' directory to {dag_dst_path}")
    _copy_src_dir_to_dst_dir(config_src_path, dag_dst_path)


class DbtProfile(TypedDict):
    target: str
    outputs: Dict[str, Dict[str, Any]]


def _generate_profile_dict(env: str) -> Dict[str, DbtProfile]:
    copy_config_dir_to_build_dir()
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
    """
    Generates and saves ``profiles.yml`` file at ``build/profiles/{env}``.

    :param env: str
    :return: Path to ``build/profiles/{env}``
    """
    echo_info("Generating .profiles.yml")
    profile = _generate_profile_dict(env)
    profiles_path = profiles_build_path(env)

    profiles_path.parent.mkdir(parents=True, exist_ok=True)
    with open(profiles_path, "w") as profiles:
        yaml.dump(profile, profiles, default_flow_style=False)

    echo_subinfo(f"Generated .profiles.yml in {profiles_path}")

    return profiles_path.parent
