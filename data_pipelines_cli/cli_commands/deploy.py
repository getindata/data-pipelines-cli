import subprocess
import sys
from typing import Optional

import click

from ..cli_constants import BUILD_DIR, GS_BUCKET_ENV
from ..cli_utils import (
    echo_error,
    echo_info,
    echo_subinfo,
    get_argument_or_environment_variable,
)
from ..data_structures import DockerArgs


def _docker_push(docker_args: DockerArgs):
    try:
        import docker
    except ModuleNotFoundError:
        echo_error(
            "'docker' not installed. Run 'pip install data-pipelines-cli[docker]'"
        )
        sys.exit(1)

    echo_info("Pushing Docker image")
    docker_client = docker.from_env()
    for line in docker_client.images.push(
        repository=docker_args.repository,
        tag=docker_args.docker_tag(),
        stream=True,
    ):
        echo_subinfo(line)


def _datahub_ingest():
    try:
        import datahub  # noqa: F401
    except ModuleNotFoundError:
        echo_error(
            "'datahub' not installed. Run 'pip install data-pipelines-cli[datahub]'"
        )
        sys.exit(1)

    echo_info("Ingesting datahub metadata")
    subprocess.run(
        [
            "datahub",
            "ingest",
            "-c",
            str(BUILD_DIR.joinpath("dag", "config", "base", "datahub.yml")),
        ]
    )
    return True


def _sync_bucket(gs_bucket: str) -> None:
    build_dag_path = BUILD_DIR.joinpath("dag")

    echo_info("Syncing GCP Bucket")
    subprocess.run(
        [
            "gsutil",
            "rsync",
            "-d",
            "-r",
            str(build_dag_path),
            f"{gs_bucket}/dags/pipeline-example",
        ]
    )


def deploy(
    repository: Optional[str],
    gs_bucket: Optional[str],
    docker_push: bool,
    datahub_ingest: bool,
) -> None:
    gs_bucket = get_argument_or_environment_variable(
        gs_bucket, "gs-bucket", GS_BUCKET_ENV
    )

    if docker_push:
        docker_args = DockerArgs(repository)
        _docker_push(docker_args)

    if datahub_ingest:
        _datahub_ingest()

    _sync_bucket(gs_bucket)


@click.command(name="deploy")
@click.option("--repository", default=None)
@click.option("--gs-bucket", default=None)
@click.option("--docker-push", is_flag=True, default=False)
@click.option("--datahub-ingest", is_flag=True, default=False)
def deploy_command(
    repository: Optional[str],
    gs_bucket: Optional[str],
    docker_push: bool,
    datahub_ingest: bool,
) -> None:
    deploy(repository, gs_bucket, docker_push, datahub_ingest)
