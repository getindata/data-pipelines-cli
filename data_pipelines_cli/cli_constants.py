import pathlib

CONFIGURATION_PATH: pathlib.Path = pathlib.Path.home().joinpath(".dp.yml")
DATAHUB_URL_ENV: str = "DATAHUB_URL"
IMAGE_TAG_TO_REPLACE: str = "<IMAGE_TAG>"
DOCKER_REPOSITORY_URL_TO_REPLACE: str = "<DOCKER_REPOSITORY_URL>"
INGEST_ENDPOINT_TO_REPLACE: str = "<INGEST_ENDPOINT>"
BUILD_DIR: pathlib.Path = pathlib.Path.cwd().joinpath("build")
