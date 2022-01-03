import pathlib

from data_pipelines_cli.data_structures import DataPipelinesConfig

#:
IMAGE_TAG_TO_REPLACE: str = "<IMAGE_TAG>"
#: Name of the environment and dbt target to use for a local machine
PROFILE_NAME_LOCAL_ENVIRONMENT = "local"
#: Name of the dbt target to use for a remote machine
PROFILE_NAME_ENV_EXECUTION = "env_execution"
AVAILABLE_ENVS = [PROFILE_NAME_LOCAL_ENVIRONMENT, PROFILE_NAME_ENV_EXECUTION]

#: Content of the config file created by `dp init` command if no template path
#: is provided
DEFAULT_GLOBAL_CONFIG: DataPipelinesConfig = {
    "templates": {},
    "vars": {},
}

CONFIGURATION_PATH: pathlib.Path = pathlib.Path.home().joinpath(".dp.yml")
BUILD_DIR: pathlib.Path = pathlib.Path.cwd().joinpath("build")


def get_dbt_profiles_env_name(env: str) -> str:
    """
    Given a name of the environment, returns one of target names expected by
    the `profiles.yml` file

    :param env: Name of the environment
    :type env: str
    :return: Name of the `target` to be used in `profiles.yml`
    """
    return (
        PROFILE_NAME_LOCAL_ENVIRONMENT
        if env == PROFILE_NAME_LOCAL_ENVIRONMENT
        else PROFILE_NAME_ENV_EXECUTION
    )
