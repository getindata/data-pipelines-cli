import sys
from typing import Dict, Optional

import yaml

from data_pipelines_cli.cli_utils import (
    echo_warning,
    get_argument_or_environment_variable_or_throw,
)
from data_pipelines_cli.errors import DataPipelinesError, NoConfigFileError
from data_pipelines_cli.io_utils import git_revision_hash

if sys.version_info >= (3, 8):
    from typing import TypedDict  # pylint: disable=no-name-in-module
else:
    from typing_extensions import TypedDict


class TemplateConfig(TypedDict):
    """POD representing value referenced in the `templates` section of
    the `.dp.yml` config file"""

    template_name: str
    """Name of the template"""
    template_path: str
    """Local path or Git URI to the template repository"""


class DataPipelinesConfig(TypedDict):
    """POD representing `.dp.yml` config file"""

    templates: Dict[str, TemplateConfig]
    """Dictionary of saved templates to use in `dp create` command"""
    vars: Dict[str, str]
    """Variables to be passed to dbt as `--vars` argument"""


def read_config() -> Optional[DataPipelinesConfig]:
    """
    Parses `.dp.yml` config file, if it exists

    :return: POD representing `.dp.yml` config file, if it exists
    :rtype: Optional[DataPipelinesConfig]
    """
    # Avoiding a dependency loop between `cli_constants` and `data_structures`
    from data_pipelines_cli.cli_constants import CONFIGURATION_PATH

    if not CONFIGURATION_PATH.is_file():
        echo_warning(
            "No configuration file found. Run 'dp init' to create it.",
        )
        return None

    with open(CONFIGURATION_PATH, "r") as f:
        return yaml.safe_load(f)


def read_config_or_throw() -> DataPipelinesConfig:
    """
    Parses `.dp.yml` config file, if it exists. Otherwise, raises
    :exc:`.NoConfigFileError`

    :return: POD representing `.dp.yml` config file
    :rtype: DataPipelinesConfig
    :raises NoConfigFileError: `.dp.yml` file not found
    """

    config = read_config()
    if not config:
        raise NoConfigFileError()
    return config


class DockerArgs:
    """Arguments required by the Docker to make a push to the repository

    :raises DataPipelinesError: *repository* variable not set or git hash not found
    """

    repository: str
    """URI of the Docker images repository"""
    commit_sha: str
    """Long hash of the current Git revision. Used as an image tag"""

    def __init__(self, docker_repository_uri: Optional[str]) -> None:
        self.repository = get_argument_or_environment_variable_or_throw(
            docker_repository_uri, "repository", "REPOSITORY_URL"
        )
        commit_sha = git_revision_hash()
        if not commit_sha:
            raise DataPipelinesError("Could not get git revision hash.")
        self.commit_sha = commit_sha

    def docker_build_tag(self) -> str:
        """
        :return: Tag for Docker Python API build command.
        :rtype: str
        """
        return f"{self.repository}:{self.commit_sha}"
