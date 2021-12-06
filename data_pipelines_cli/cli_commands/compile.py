import pathlib
import shutil
import sys
from typing import Optional

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
)
from ..data_structures import DockerArgs
from ..io_utils import replace
from .dbt import dbt


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


def _docker_build(docker_args: DockerArgs):
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
    echo_info("Running dbt commands:")

    echo_subinfo("dbt deps")
    dbt(("deps",), env)

    echo_subinfo("dbt compile")
    dbt(("compile",), env)

    echo_subinfo("dbt docs generate")
    dbt(("docs", "generate"), env)

    echo_subinfo("dbt source freshness")
    dbt(("source", "freshness"), env)


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


def _copy_src_dir_to_dst_dir(src_dir: pathlib.Path, dst_dir: pathlib.Path) -> None:
    # It has to be deleted before copying, as `copytree` complains with
    # `FileExistsError`
    if pathlib.Path.exists(dst_dir):
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)


def _copy_dag_dir_to_build_dir() -> None:
    dag_src_path = pathlib.Path.cwd().joinpath("dag")
    dag_dst_path = BUILD_DIR.joinpath("dag")
    _copy_src_dir_to_dst_dir(dag_src_path, dag_dst_path)


def _copy_config_dir_to_build_dir() -> None:
    config_src_path = pathlib.Path.cwd().joinpath("config")
    dag_dst_path = BUILD_DIR.joinpath("dag", "config")
    echo_info(f"Copying 'config' directory to {dag_dst_path}")
    _copy_src_dir_to_dst_dir(config_src_path, dag_dst_path)


def compile_project(
    repository: Optional[str], datahub: Optional[str], docker_build: bool, env: str
) -> None:
    datahub_address = get_argument_or_environment_variable(
        datahub, "datahub", DATAHUB_URL_ENV
    )
    docker_args = DockerArgs(repository)

    _copy_dag_dir_to_build_dir()
    _copy_config_dir_to_build_dir()

    k8s_config: pathlib.Path = BUILD_DIR.joinpath("dag", "config", "base", "k8s.yml")
    _replace_image_tag(k8s_config, docker_args)
    _replace_docker_repository_url(k8s_config, docker_args)

    if docker_build:
        _docker_build(docker_args)
    _dbt_compile(env)
    _copy_dbt_manifest()

    _replace_datahub_address(datahub_address)


@click.command(name="compile")
@click.option("--repository", default=None)
@click.option("--datahub", default=None)
@click.option("--docker-build", is_flag=True, default=False)
@click.option("--env", default="gitlab")
def compile_project_command(
    repository: Optional[str], datahub: Optional[str], docker_build: bool, env: str
) -> None:
    compile_project(repository, datahub, docker_build, env)
