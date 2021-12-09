import pathlib

from data_pipelines_cli.data_structures import DataPipelinesConfig

DATAHUB_URL_ENV: str = "DATAHUB_URL"
IMAGE_TAG_TO_REPLACE: str = "<IMAGE_TAG>"
DOCKER_REPOSITORY_URL_TO_REPLACE: str = "<DOCKER_REPOSITORY_URL>"
INGEST_ENDPOINT_TO_REPLACE: str = "<INGEST_ENDPOINT>"

DEFAULT_GLOBAL_CONFIG: DataPipelinesConfig = {
    "templates": {},
    "vars": {},
}

CONFIGURATION_PATH: pathlib.Path = pathlib.Path.home().joinpath(".dp.yml")
BUILD_DIR: pathlib.Path = pathlib.Path.cwd().joinpath("build")


def profiles_build_path(env: str) -> pathlib.Path:
    return BUILD_DIR.joinpath("profiles", env, "profiles.yml")
