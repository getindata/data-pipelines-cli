import pathlib
import shutil

import click

from ..cli_constants import BUILD_DIR, IMAGE_TAG_TO_REPLACE
from ..cli_utils import echo_info
from ..config_generation import (
    copy_config_dir_to_build_dir,
    copy_dag_dir_to_build_dir,
    generate_profiles_yml,
)
from ..data_structures import DockerArgs
from ..dbt_utils import run_dbt_command
from ..errors import DockerNotInstalledError
from ..io_utils import replace


def _replace_image_tag(k8s_config: pathlib.Path, docker_args: DockerArgs) -> None:
    echo_info(
        f"Replacing {IMAGE_TAG_TO_REPLACE} with commit SHA = {docker_args.commit_sha}"
    )
    replace(k8s_config, IMAGE_TAG_TO_REPLACE, docker_args.commit_sha)


def _docker_build(docker_args: DockerArgs) -> None:
    """
    :param docker_args: Arguments required by the Docker to make a push to \
        the repository
    :raises DataPipelinesError: Docker not installed
    """
    try:
        import docker
    except ModuleNotFoundError:
        raise DockerNotInstalledError()

    echo_info("Building Docker image")
    docker_client = docker.from_env()
    docker_tag = docker_args.docker_build_tag()
    _, logs_generator = docker_client.images.build(path=".", tag=docker_tag)
    click.echo(
        "".join(
            map(
                lambda log: log["stream"],
                filter(lambda log: "stream" in log, logs_generator),
            )
        )
    )


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


def _replace_k8s_settings(docker_args: DockerArgs) -> None:
    k8s_config: pathlib.Path = BUILD_DIR.joinpath("dag", "config", "base", "k8s.yml")
    _replace_image_tag(k8s_config, docker_args)


def compile_project(
    env: str,
    docker_build: bool = False,
) -> None:
    """
    Create local working directories and build artifacts

    :param env: Name of the environment
    :type env: str
    :param docker_build: Whether to build a Docker image
    :type docker_build: bool
    :raises DataPipelinesError:
    """
    copy_dag_dir_to_build_dir()
    copy_config_dir_to_build_dir()

    docker_args = DockerArgs(env)
    _replace_k8s_settings(docker_args)

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
def compile_project_command(
    env: str,
    docker_build: bool,
) -> None:
    compile_project(env, docker_build)
