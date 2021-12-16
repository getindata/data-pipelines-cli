from __future__ import annotations

import os
import pathlib
import shutil
import sys
from typing import Any, Dict, Union

import yaml

from .cli_constants import (
    AVAILABLE_ENVS,
    BUILD_DIR,
    PROFILE_NAME_ENV_EXECUTION,
    get_dbt_profiles_env_name,
)
from .cli_utils import echo_info, echo_subinfo, echo_warning

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


# Heavily based on `config_utils.py` from
# https://github.com/getindata/dbt-airflow-manifest-parser
def read_dictionary_from_config_directory(
    dag_path: Union[str, os.PathLike[str]], env: str, file_name: str
) -> Dict[str, Any]:
    return dict(
        _read_env_config(dag_path, "base", file_name),
        **_read_env_config(dag_path, env, file_name),
    )


def _read_env_config(
    dag_path: Union[str, os.PathLike[str]], env: str, file_name: str
) -> Dict[str, Any]:
    config_file_path = pathlib.Path(dag_path).joinpath("config", env, file_name)
    if config_file_path.exists():
        return _read_yaml_file(config_file_path)
    echo_warning("Missing config file: " + str(config_file_path))
    return {}


def _read_yaml_file(file_path: Union[str, os.PathLike[str]]) -> Dict[str, Any]:
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


class DbtProfile(TypedDict):
    target: str
    outputs: Dict[str, Dict[str, Any]]


def _generate_profile_dict(env: str) -> Dict[str, DbtProfile]:
    dbt_env_config = read_dictionary_from_config_directory(
        BUILD_DIR.joinpath("dag"), env, "dbt.yml"
    )
    dbt_target: str = dbt_env_config["target"]
    dbt_target_type: str = dbt_env_config["target_type"]
    target_type_config = read_dictionary_from_config_directory(
        BUILD_DIR.joinpath("dag"), env, f"{dbt_target_type}.yml"
    )
    target_type_config["type"] = dbt_target_type

    if dbt_target not in AVAILABLE_ENVS:
        echo_warning(
            f"dbt target {dbt_target} is not one of {AVAILABLE_ENVS}. "
            "It can cause errors when running or deploying your project. "
            f"Consider changing target in your 'config/{env}/dbt.yml' to "
            f"{PROFILE_NAME_ENV_EXECUTION}."
        )

    return {
        dbt_target_type: {
            "target": dbt_target,
            "outputs": {dbt_target: target_type_config},
        }
    }


def generate_profiles_yml(env: str, copy_config_dir: bool = True) -> pathlib.Path:
    """
    Generates and saves ``profiles.yml`` file at ``build/profiles/local`` or
    ``build/profiles/env_execution``, depending on `env` argument.

    :param env: str
    :param copy_config_dir: bool
    :return: Path to ``build/profiles/{env}``
    """
    if copy_config_dir:
        copy_config_dir_to_build_dir()
    echo_info("Generating profiles.yml")
    profile = _generate_profile_dict(env)

    profile_name = get_dbt_profiles_env_name(env)
    profiles_path = BUILD_DIR.joinpath("profiles", profile_name, "profiles.yml")
    profiles_path.parent.mkdir(parents=True, exist_ok=True)
    with open(profiles_path, "w") as profiles:
        yaml.dump(profile, profiles, default_flow_style=False)

    echo_subinfo(f"Generated profiles.yml in {profiles_path}")

    return profiles_path.parent
