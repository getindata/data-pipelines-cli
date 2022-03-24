import pathlib

from data_pipelines_cli.cli_constants import BUILD_DIR


def find_datahub_config_file(env: str) -> pathlib.Path:
    if BUILD_DIR.joinpath("dag", "config", env, "datahub.yml").is_file():
        return BUILD_DIR.joinpath("dag", "config", env, "datahub.yml")
    return BUILD_DIR.joinpath("dag", "config", "base", "datahub.yml")
