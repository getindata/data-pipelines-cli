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
    """Recursively copy `dag` directory to `build/dag` working directory."""
    dag_src_path = pathlib.Path.cwd().joinpath("dag")
    dag_dst_path = BUILD_DIR.joinpath("dag")
    _copy_src_dir_to_dst_dir(dag_src_path, dag_dst_path)


def copy_config_dir_to_build_dir() -> None:
    """Recursively copy `config` directory to `build/dag/config` working directory."""
    config_src_path = pathlib.Path.cwd().joinpath("config")
    dag_dst_path = BUILD_DIR.joinpath("dag", "config")
    echo_info(f"Copying 'config' directory to {dag_dst_path}")
    _copy_src_dir_to_dst_dir(config_src_path, dag_dst_path)


# Heavily based on `config_utils.py` from
# https://github.com/getindata/dbt-airflow-manifest-parser
def read_dictionary_from_config_directory(
    config_path: Union[str, os.PathLike[str]], env: str, file_name: str
) -> Dict[str, Any]:
    """
    Read dictionaries out of *file_name* in both `base` and *env* directories,
    and compile them into one. Values from *env* directory get precedence over
    `base` ones.

    :param config_path: Path to the `config` directory
    :type config_path: Union[str, os.PathLike[str]]
    :param env: Name of the environment
    :type env: str
    :param file_name: Name of the YAML file to parse dictionary from
    :type file_name: str
    :return: Compiled dictionary
    :rtype: Dict[str, Any]
    """
    return dict(
        _read_env_config(config_path, "base", file_name),
        **_read_env_config(config_path, env, file_name),
    )


def _read_env_config(
    config_path: Union[str, os.PathLike[str]], env: str, file_name: str
) -> Dict[str, Any]:
    config_file_path = pathlib.Path(config_path).joinpath("config", env, file_name)
    if config_file_path.exists():
        return _read_yaml_file(config_file_path)
    echo_warning("Missing config file: " + str(config_file_path))
    return {}


def _read_yaml_file(file_path: Union[str, os.PathLike[str]]) -> Dict[str, Any]:
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


class DbtProfile(TypedDict):
    """POD representing dbt's `profiles.yml` file."""

    target: str
    """Name of the `target` for dbt to run"""
    outputs: Dict[str, Dict[str, Any]]
    """Dictionary of a warehouse data and credentials, referenced by `target` name"""


def generate_profiles_dict(env: str, copy_config_dir: bool) -> Dict[str, DbtProfile]:
    """
    Generate and save ``profiles.yml`` file at ``build/profiles/local`` or
    ``build/profiles/env_execution``, depending on `env` argument.

    :param env: Name of the environment
    :type env: str
    :param copy_config_dir: Whether to copy ``config`` directory to ``build`` \
        working directory
    :type copy_config_dir: bool
    :return: Dictionary representing data to be saved in ``profiles.yml``
    :rtype: Dict[str, DbtProfile]
    """
    if copy_config_dir:
        copy_config_dir_to_build_dir()

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


def get_profiles_dir_build_path(env: str) -> pathlib.Path:
    """
    Returns path to ``build/profiles/<profile_name>/``, depending on `env` argument.

    :param env: Name of the environment
    :type env: str
    :return:
    :rtype: pathlib.Path
    """
    profile_name = get_dbt_profiles_env_name(env)
    return BUILD_DIR.joinpath("profiles", profile_name)


def generate_profiles_yml(env: str, copy_config_dir: bool = True) -> pathlib.Path:
    """
    Generate and save ``profiles.yml`` file at ``build/profiles/local`` or
    ``build/profiles/env_execution``, depending on `env` argument.

    :param env: Name of the environment
    :type env: str
    :param copy_config_dir: Whether to copy ``config`` directory to ``build`` \
        working directory
    :type copy_config_dir: bool
    :return: Path to ``build/profiles/{env}``
    :rtype: pathlib.Path
    """
    echo_info("Generating profiles.yml")
    profile = generate_profiles_dict(env, copy_config_dir)

    profiles_path = get_profiles_dir_build_path(env)
    profiles_path.mkdir(parents=True, exist_ok=True)
    with open(profiles_path.joinpath("profiles.yml"), "w") as profiles:
        yaml.dump(profile, profiles, default_flow_style=False)
    echo_subinfo(f"Generated profiles.yml in {profiles_path}")

    return profiles_path
