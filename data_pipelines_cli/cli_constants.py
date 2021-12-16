import pathlib

from data_pipelines_cli.data_structures import DataPipelinesConfig

DATAHUB_URL_ENV: str = "DATAHUB_URL"
IMAGE_TAG_TO_REPLACE: str = "<IMAGE_TAG>"
DOCKER_REPOSITORY_URL_TO_REPLACE: str = "<DOCKER_REPOSITORY_URL>"
INGEST_ENDPOINT_TO_REPLACE: str = "<INGEST_ENDPOINT>"
PROFILE_NAME_LOCAL_ENVIRONMENT = "local"
PROFILE_NAME_ENV_EXECUTION = "env_execution"
AVAILABLE_ENVS = [PROFILE_NAME_LOCAL_ENVIRONMENT, PROFILE_NAME_ENV_EXECUTION]

DEFAULT_GLOBAL_CONFIG: DataPipelinesConfig = {
    "templates": {},
    "vars": {},
}

CONFIGURATION_PATH: pathlib.Path = pathlib.Path.home().joinpath(".dp.yml")
BUILD_DIR: pathlib.Path = pathlib.Path.cwd().joinpath("build")


def get_dbt_profiles_env_name(env: str) -> str:
    return (
        PROFILE_NAME_LOCAL_ENVIRONMENT
        if env == PROFILE_NAME_LOCAL_ENVIRONMENT
        else PROFILE_NAME_ENV_EXECUTION
    )
