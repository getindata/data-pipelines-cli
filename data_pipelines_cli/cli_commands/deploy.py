import io
import json
from typing import Any, Dict, Optional, cast

import click
import yaml

from ..cli_constants import BUILD_DIR
from ..cli_utils import echo_info, subprocess_run
from ..config_generation import read_dictionary_from_config_directory
from ..data_structures import DockerArgs
from ..errors import (
    AirflowDagsPathKeyError,
    DataPipelinesError,
    DependencyNotInstalledError,
    DockerNotInstalledError,
)
from ..filesystem_utils import LocalRemoteSync


class DeployCommand:
    """A class used to push and deploy the project to the remote machine"""

    docker_args: Optional[DockerArgs]
    """Arguments required by the Docker to make a push to the repository.
    If set to `None`, :meth:`deploy` will not make a push"""
    datahub_ingest: bool
    """Whether to ingest DataHub metadata"""
    blob_address_path: str
    """URI of the cloud storage to send build artifacts to"""
    provider_kwargs_dict: Dict[str, Any]
    """Dictionary of arguments required by a specific cloud storage provider,
    e.g. path to a token, username, password, etc."""

    def __init__(
        self,
        env: str,
        docker_push: bool,
        dags_path: Optional[str],
        provider_kwargs_dict: Optional[Dict[str, Any]],
        datahub_ingest: bool,
    ) -> None:
        self.docker_args = DockerArgs(env) if docker_push else None
        self.datahub_ingest = datahub_ingest
        self.provider_kwargs_dict = provider_kwargs_dict or {}

        try:
            self.blob_address_path = (
                dags_path
                or read_dictionary_from_config_directory(
                    BUILD_DIR.joinpath("dag"), "base", "airflow.yml"
                )["dags_path"]
            )
        except KeyError as key_error:
            raise AirflowDagsPathKeyError from key_error

    def deploy(self) -> None:
        """Push and deploy the project to the remote machine

        :raises DependencyNotInstalledError: DataHub or Docker not installed
        :raises DataPipelinesError: Error while pushing Docker image
        """
        if self.docker_args:
            self._docker_push()

        if self.datahub_ingest:
            self._datahub_ingest()

        self._sync_bucket()

    def _docker_push(self) -> None:
        """
        :raises DockerNotInstalledError: Docker not installed
        :raises DataPipelinesError: Error while pushing Docker image
        """
        try:
            import docker
        except ModuleNotFoundError:
            raise DockerNotInstalledError()

        echo_info("Pushing Docker image")
        docker_client = docker.from_env()
        docker_args = cast(DockerArgs, self.docker_args)
        for line in docker_client.images.push(
            repository=docker_args.repository,
            tag=docker_args.commit_sha,
            stream=True,
            decode=True,
        ):
            click.echo(line)

            if "error" in line:
                raise DataPipelinesError(
                    "Error raised when pushing Docker image. Ensure that "
                    "Docker image you try to push exists. Maybe try running "
                    "'dp compile' first?"
                )

    @staticmethod
    def _datahub_ingest() -> None:
        """:raises DependencyNotInstalledError: DataHub not installed"""
        try:
            import datahub  # noqa: F401
        except ModuleNotFoundError:
            raise DependencyNotInstalledError("datahub")

        echo_info("Ingesting datahub metadata")
        subprocess_run(
            [
                "datahub",
                "ingest",
                "-c",
                str(BUILD_DIR.joinpath("dag", "config", "base", "datahub.yml")),
            ]
        )

    def _sync_bucket(self) -> None:
        echo_info("Syncing Bucket")
        LocalRemoteSync(
            BUILD_DIR.joinpath("dag"), self.blob_address_path, self.provider_kwargs_dict
        ).sync(delete=True)


@click.command(
    name="deploy",
    help="Push and deploy the project to the remote machine",
)
@click.option("--env", default="base", type=str, help="Name of the environment")
@click.option("--dags-path", required=False, help="Remote storage URI")
@click.option(
    "--blob-args",
    required=False,
    type=click.File("r"),
    help="Path to JSON or YAML file with arguments that should be passed to "
    "your Bucket/blob provider",
)
@click.option(
    "--docker-push",
    type=bool,
    is_flag=True,
    default=False,
    help="Whether to push image to the Docker repository",
)
@click.option(
    "--datahub-ingest",
    is_flag=True,
    default=False,
    help="Whether to ingest DataHub metadata",
)
def deploy_command(
    env: str,
    dags_path: Optional[str],
    blob_args: Optional[io.TextIOWrapper],
    docker_push: bool,
    datahub_ingest: bool,
) -> None:
    if blob_args:
        try:
            provider_kwargs_dict = json.load(blob_args)
        except json.JSONDecodeError:
            blob_args.seek(0)
            provider_kwargs_dict = yaml.safe_load(blob_args)
    else:
        provider_kwargs_dict = None

    DeployCommand(
        env,
        docker_push,
        dags_path,
        provider_kwargs_dict,
        datahub_ingest,
    ).deploy()
