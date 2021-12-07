import pathlib
import shutil
import sys
from typing import Optional, Tuple

import click

from ..cli_constants import (
    BUILD_DIR,
    DATAHUB_URL_ENV,
    DOCKER_REPOSITORY_URL_TO_REPLACE,
    IMAGE_TAG_TO_REPLACE,
    INGEST_ENDPOINT_TO_REPLACE,
)
from ..cli_utils import (
    echo_error,
    echo_info,
    echo_subinfo,
    get_argument_or_environment_variable,
    subprocess_run,
)
from ..config_generation import (
    copy_config_dir_to_build_dir,
    copy_dag_dir_to_build_dir,
    generate_profiles_yml,
)
from ..data_structures import DockerArgs
from ..io_utils import replace


def dbt(
    command: Tuple[str, ...], env: str, profiles_path: Optional[pathlib.Path]
) -> None:
    command_str = " ".join(list(command))
    echo_subinfo(f"dbt {command_str}")
    profiles_path = profiles_path or generate_profiles_yml(env)
    subprocess_run(
        ["dbt", *command, "--profiles-dir", str(profiles_path), "--target", env]
    )


def _replace_image_tag(k8s_config: pathlib.Path, docker_args: DockerArgs) -> None:
    echo_info(f"Replacing <IMAGE_TAG> with commit SHA = {docker_args.commit_sha}")
    replace(k8s_config, IMAGE_TAG_TO_REPLACE, docker_args.commit_sha)


def _replace_docker_repository_url(
    k8s_config: pathlib.Path, docker_args: DockerArgs
) -> None:
    echo_info(
        "Replacing <DOCKER_REPOSITORY_URL> with repository URL = "
        f"{docker_args.repository}"
    )
    replace(k8s_config, DOCKER_REPOSITORY_URL_TO_REPLACE, docker_args.repository)


def _docker_build(docker_args: DockerArgs) -> None:
    try:
        import docker
    except ModuleNotFoundError:
        echo_error(
            "'docker' not installed. Run 'pip install data-pipelines-cli[docker]'"
        )
        sys.exit(1)

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
    profiles_path = generate_profiles_yml(env)
    echo_info("Running dbt commands:")
    dbt(("deps",), env, profiles_path)
    dbt(("compile",), env, profiles_path)
    dbt(("docs", "generate"), env, profiles_path)
    dbt(("source", "freshness"), env, profiles_path)


def _copy_dbt_manifest() -> None:
    echo_info("Copying DBT manifest")
    shutil.copyfile(
        pathlib.Path.cwd().joinpath("target", "manifest.json"),
        BUILD_DIR.joinpath("dag", "manifest.json"),
    )


def _replace_datahub_address(datahub_address: str) -> None:
    echo_info(f"Replacing INGEST_ENDPOINT with datahub address = {datahub_address}")
    replace(
        BUILD_DIR.joinpath("dag", "config", "base", "datahub.yml"),
        INGEST_ENDPOINT_TO_REPLACE,
        datahub_address,
    )


def compile_project(
    repository: Optional[str],
    datahub: Optional[str],
    docker_build: bool,
    env: str,
) -> None:
    datahub_address = get_argument_or_environment_variable(
        datahub, "datahub", DATAHUB_URL_ENV
    )
    docker_args = DockerArgs(repository)

    copy_dag_dir_to_build_dir()
    copy_config_dir_to_build_dir()

    k8s_config: pathlib.Path = BUILD_DIR.joinpath("dag", "config", "base", "k8s.yml")
    _replace_image_tag(k8s_config, docker_args)
    _replace_docker_repository_url(k8s_config, docker_args)

    if docker_build:
        _docker_build(docker_args)
    _dbt_compile(env)
    _copy_dbt_manifest()

    _replace_datahub_address(datahub_address)


@click.command(name="compile")
@click.option("--env", required=True)
@click.option("--repository", default=None)
@click.option("--datahub", default=None)
@click.option("--docker-build", is_flag=True, default=False)
def compile_project_command(
    env: str,
    repository: Optional[str],
    datahub: Optional[str],
    docker_build: bool,
) -> None:
    compile_project(repository, datahub, docker_build, env)
