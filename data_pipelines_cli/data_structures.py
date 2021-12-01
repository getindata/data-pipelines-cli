import sys
from typing import Dict, Optional

import yaml

from data_pipelines_cli.cli_constants import CONFIGURATION_PATH
from data_pipelines_cli.cli_utils import (
    echo_error,
    get_argument_or_environment_variable,
)
from data_pipelines_cli.io_utils import git_revision_hash

if sys.version_info >= (3, 8):
    from typing import TypedDict  # pylint: disable=no-name-in-module
else:
    from typing_extensions import TypedDict


class TemplateConfig(TypedDict):
    template_name: str
    template_path: str


class DataPipelinesConfig(TypedDict):
    username: str
    templates: Dict[str, TemplateConfig]


def read_config_or_exit() -> DataPipelinesConfig:
    if not CONFIGURATION_PATH.is_file():
        echo_error(
            "No configuration file found. Run 'dp init' to create it.",
        )
        sys.exit(1)

    with open(CONFIGURATION_PATH, "r") as f:
        return yaml.safe_load(f)


class DockerArgs:
    repository: str
    commit_sha: str

    def __init__(self, repository: Optional[str]):
        self.repository = get_argument_or_environment_variable(
            repository, "repository", "REPOSITORY_URL"
        )
        commit_sha = git_revision_hash()
        if not commit_sha:
            echo_error("Could not get git revision hash.")
            sys.exit(1)
        self.commit_sha = commit_sha

    def docker_tag(self) -> str:
        return f"{self.repository}:{self.commit_sha}"
