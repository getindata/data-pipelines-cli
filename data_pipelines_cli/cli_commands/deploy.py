import io
import json
from typing import Any, Dict, Optional, cast

import click
import yaml

from ..airbyte_utils import AirbyteFactory
from ..bi_utils import BiAction, bi
from ..cli_configs import find_datahub_config_file
from ..cli_constants import BUILD_DIR
from ..cli_utils import echo_error, echo_info, subprocess_run
from ..config_generation import read_dictionary_from_config_directory
from ..data_structures import DockerArgs
from ..docker_response_reader import DockerResponseReader
from ..errors import (
    AirflowDagsPathKeyError,
    DataPipelinesError,
    DependencyNotInstalledError,
    DockerErrorResponseError,
    DockerNotInstalledError,
)
from ..filesystem_utils import LocalRemoteSync


class DeployCommand:
    """A class used to push and deploy the project to the remote machine."""

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
    env: str
    bi_git_key_path: str
    """Path to JSON file containing key for GCP service account
    used to communicate with IAP-secured applications"""
    gcp_sa_key_path: Optional[str]
    """Client ID of Airbyte IAP-secured instance"""
    airbyte_iap_client_id: Optional[str]

    def __init__(
        self,
        env: str,
        docker_push: bool,
        dags_path: Optional[str],
        provider_kwargs_dict: Optional[Dict[str, Any]],
        datahub_ingest: bool,
        bi_git_key_path: str,
        gcp_sa_key_path: Optional[str] = None,
        airbyte_iap_client_id: Optional[str] = None,
    ) -> None:
        self.docker_args = DockerArgs(env, None, {}) if docker_push else None
        self.datahub_ingest = datahub_ingest
        self.provider_kwargs_dict = provider_kwargs_dict or {}
        self.env = env
        self.bi_git_key_path = bi_git_key_path
        self.gcp_sa_key_path = gcp_sa_key_path
        self.airbyte_iap_client_id = airbyte_iap_client_id

        try:
            self.blob_address_path = (
                dags_path
                or read_dictionary_from_config_directory(
                    BUILD_DIR.joinpath("dag"),
                    env,
                    "airflow.yml",
                )["dags_path"]
            )
        except KeyError as key_error:
            raise AirflowDagsPathKeyError from key_error

        self.enable_ingest = read_dictionary_from_config_directory(
            BUILD_DIR.joinpath("dag"), env, "ingestion.yml"
        ).get("enable", False)

    def deploy(self) -> None:
        """Push and deploy the project to the remote machine.

        :raises DependencyNotInstalledError: DataHub or Docker not installed
        :raises DataPipelinesError: Error while pushing Docker image
        """
        if self.docker_args:
            self._docker_push()

        if self.datahub_ingest:
            self._datahub_ingest()

        if self.enable_ingest:
            self._enable_ingest()

        self._bi_push()

        self._sync_bucket()

    def _bi_push(self) -> None:
        bi(self.env, BiAction.DEPLOY, self.bi_git_key_path)

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

        try:
            DockerResponseReader(
                docker_client.images.push(
                    repository=docker_args.repository,
                    tag=docker_args.image_tag,
                    stream=True,
                    decode=True,
                )
            ).click_echo_ok_responses()
        except DockerErrorResponseError as err:
            echo_error(err.message)
            raise DataPipelinesError(
                "Error raised when pushing Docker image. Ensure that "
                "Docker image you try to push exists. Maybe try running "
                "'dp compile' first?"
            )

    def _datahub_ingest(self) -> None:
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
                str(find_datahub_config_file(self.env)),
            ]
        )

    def _enable_ingest(self) -> None:
        echo_info("Ingesting airbyte config")
        airbyte_config_path = AirbyteFactory.find_config_file(self.env, "airbyte")
        AirbyteFactory(
            airbyte_config_path=airbyte_config_path,
            iap_enabled=True,
            airbyte_iap_client_id=self.airbyte_iap_client_id,
            gcp_sa_key_path=self.gcp_sa_key_path,
        ).create_update_connections()

    def _sync_bucket(self) -> None:
        echo_info("Syncing Bucket")
        LocalRemoteSync(
            BUILD_DIR.joinpath("dag"), self.blob_address_path, self.provider_kwargs_dict
        ).sync(delete=True)


@click.command(
    name="deploy",
    help="Push and deploy the project to the remote machine",
)
@click.option("--env", default="base", show_default=True, type=str, help="Name of the environment")
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
@click.option(
    "--bi-git-key-path",
    type=str,
    required=False,
    help="Path to the key with write access to repo",
)
@click.option(
    "--gcp-sa-key-path",
    type=str,
    required=False,
    help="Path to the key file of GCP service account for communication with IAP",
)
@click.option(
    "--airbyte-iap-client-id", type=str, required=False, help="IAP Client ID of Airbyte instance"
)
def deploy_command(
    env: str,
    dags_path: Optional[str],
    blob_args: Optional[io.TextIOWrapper],
    docker_push: bool,
    datahub_ingest: bool,
    bi_git_key_path: str,
    gcp_sa_key_path: Optional[str],
    airbyte_iap_client_id: Optional[str],
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
        bi_git_key_path,
        gcp_sa_key_path,
        airbyte_iap_client_id,
    ).deploy()
