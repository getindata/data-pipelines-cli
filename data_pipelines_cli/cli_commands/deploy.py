import io
import json
import os
import pathlib
import subprocess
import sys
from typing import Dict, Optional

import click
import yaml

from ..cli_constants import BUILD_DIR
from ..cli_utils import echo_error, echo_info
from ..data_structures import DockerArgs
from ..filesystem_utils import LocalRemoteSync


class DeployCommand:
    docker_args: Optional[DockerArgs]
    datahub_ingest: bool
    blob_address_path: str
    provider_kwargs_dict: Dict[str, str]

    def __init__(
        self,
        repository: Optional[str],
        blob_address: str,
        provider_kwargs_dict: Dict[str, str],
        docker_push: bool,
        datahub_ingest: bool,
    ):
        self.docker_args = DockerArgs(repository) if docker_push else None
        self.datahub_ingest = datahub_ingest
        self.blob_address_path = os.path.join(
            blob_address, "dags", DeployCommand._get_project_name()
        )
        self.provider_kwargs_dict = provider_kwargs_dict

    def deploy(self) -> None:
        if self.docker_args:
            self._docker_push()

        if self.datahub_ingest:
            self._datahub_ingest()

        self._sync_bucket()

    @staticmethod
    def _get_project_name():
        with open(pathlib.Path().joinpath("dbt_project.yml")) as f:
            dbt_project_config = yaml.safe_load(f)
            return dbt_project_config["name"]

    def _docker_push(self):
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
            repository=self.docker_args.repository,
            tag=self.docker_args.commit_sha,
            stream=True,
        ):
            click.echo(line, nl=False)

    @staticmethod
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

    def _sync_bucket(self) -> None:
        echo_info("Syncing Bucket")
        LocalRemoteSync(
            BUILD_DIR.joinpath("dag"), self.blob_address_path, self.provider_kwargs_dict
        ).sync(delete=True)


@click.command(name="deploy")
@click.argument("address")
@click.option(
    "--blob-args",
    required=True,
    type=click.File("r"),
    help="Path to JSON or YAML file with arguments that should be passed to "
    "your Bucket/blob provider",
)
@click.option("--repository", default=None)
@click.option("--docker-push", is_flag=True, default=False)
@click.option("--datahub-ingest", is_flag=True, default=False)
def deploy_command(
    address: str,
    blob_args: io.TextIOWrapper,
    repository: Optional[str],
    docker_push: bool,
    datahub_ingest: bool,
) -> None:
    try:
        provider_kwargs_dict = json.load(blob_args)
    except json.JSONDecodeError:
        provider_kwargs_dict = yaml.safe_load(blob_args)

    DeployCommand(
        repository,
        address,
        provider_kwargs_dict,
        docker_push,
        datahub_ingest,
    ).deploy()
