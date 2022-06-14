import json
import pathlib
import shutil
from typing import Dict, Optional

import click
import yaml

from ..cli_configs import find_datahub_config_file
from ..cli_constants import BUILD_DIR, IMAGE_TAG_TO_REPLACE
from ..cli_utils import echo_info, echo_warning
from ..config_generation import (
    copy_config_dir_to_build_dir,
    copy_dag_dir_to_build_dir,
    generate_profiles_yml,
)
from ..data_structures import DockerArgs
from ..dbt_utils import read_dbt_vars_from_configs, run_dbt_command
from ..docker_response_reader import DockerResponseReader
from ..errors import DockerErrorResponseError, DockerNotInstalledError
from ..io_utils import replace
from ..jinja import replace_vars_with_values


def _docker_build(docker_args: DockerArgs) -> None:
    """
    :param docker_args: Arguments required by the Docker to make a push to \
        the repository
    :raises DataPipelinesError: Docker not installed
    """
    try:
        import docker
        import docker.errors
    except ModuleNotFoundError:
        raise DockerNotInstalledError()

    echo_info("Building Docker image")
    docker_client = docker.from_env()
    docker_tag = docker_args.docker_build_tag()
    try:
        _, logs_generator = docker_client.images.build(
            path=".", tag=docker_tag, buildargs=docker_args.build_args
        )
        DockerResponseReader(logs_generator).click_echo_ok_responses()
    except docker.errors.BuildError as err:
        build_log = "\n".join([str(log) for log in err.build_log])
        raise DockerErrorResponseError(f"{err.msg}\n{build_log}")


def _dbt_compile(env: str) -> None:
    profiles_path = generate_profiles_yml(env, False)
    echo_info("Running dbt commands:")
    run_dbt_command(("deps",), env, profiles_path)
    run_dbt_command(("compile",), env, profiles_path)
    run_dbt_command(("docs", "generate"), env, profiles_path)
    run_dbt_command(("source", "freshness"), env, profiles_path)


def _copy_dbt_manifest() -> None:
    echo_info("Copying DBT manifest")
    shutil.copyfile(
        pathlib.Path.cwd().joinpath("target", "manifest.json"),
        BUILD_DIR.joinpath("dag", "manifest.json"),
    )


def replace_image_settings(image_tag: str) -> None:
    k8s_config = BUILD_DIR.joinpath("dag", "config", "base", "execution_env.yml")
    echo_info(f"Replacing {IMAGE_TAG_TO_REPLACE} with image tag = {image_tag}")
    replace(k8s_config, IMAGE_TAG_TO_REPLACE, image_tag)


def _replace_datahub_with_jinja_vars(env: str) -> None:
    datahub_config_path: pathlib.Path = find_datahub_config_file(env)

    if not datahub_config_path.is_file():
        echo_warning(
            f"File config/base/datahub.yml does not exist in {BUILD_DIR}. "
            "Content will not be replaced."
        )
        return

    echo_info(f"Replacing Jinja variables in {datahub_config_path}.")
    with open(datahub_config_path, "r") as datahub_config_file:
        updated_config = replace_vars_with_values(
            yaml.safe_load(datahub_config_file), read_dbt_vars_from_configs(env)
        )
    with open(datahub_config_path, "w") as datahub_config_file:
        yaml.dump(updated_config, datahub_config_file)


def compile_project(
    env: str,
    docker_tag: Optional[str] = None,
    docker_build: bool = False,
    docker_build_args: Optional[Dict[str, str]] = None,
) -> None:
    """
    Create local working directories and build artifacts.

    :param env: Name of the environment
    :type env: str
    :param docker_tag: Image tag of a Docker image to create
    :type docker_tag: Optional[str]
    :param docker_build: Whether to build a Docker image
    :type docker_build: bool
    :raises DataPipelinesError:
    """
    copy_dag_dir_to_build_dir()
    copy_config_dir_to_build_dir()

    docker_args = DockerArgs(env, docker_tag, docker_build_args or {})

    replace_image_settings(docker_args.image_tag or "Empty")

    _replace_datahub_with_jinja_vars(env)

    _dbt_compile(env)
    _copy_dbt_manifest()

    if docker_build:
        _docker_build(docker_args)


@click.command(
    name="compile",
    help="Create local working directories and build artifacts",
)
@click.option(
    "--env",
    default="base",
    type=str,
    show_default=True,
    required=True,
    help="Name of the environment",
)
@click.option(
    "--docker-build",
    is_flag=True,
    default=False,
    help="Whether to build a Docker image",
)
@click.option(
    "--docker-tag", type=str, required=False, help="Image tag of a Docker image to create"
)
@click.option(
    "--docker-args", type=str, required=False, help="Args required to build project in json format"
)
def compile_project_command(
    env: str, docker_build: bool, docker_tag: Optional[str], docker_args: Optional[str]
) -> None:
    compile_project(env, docker_tag, docker_build, json.loads(docker_args or "{}"))
