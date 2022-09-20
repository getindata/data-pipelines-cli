import click

from ..cli_utils import echo_info, echo_subinfo
from ..cli_constants import BUILD_DIR
from ..config_generation import read_dictionary_from_config_directory
from ..looker_utils import generate_lookML_model, deploy_lookML_model
from ..errors import NotSuppertedBIError
from typing import Any, Dict

def read_bi_config(env: str) -> Dict[str, Any]:
    """Read BI configuration file for project (``config/{env}/bi.yml``)
    :param env: Name of the environment
    :type env: str
    :return: Dictionary with their keys
    :rtype: BiConfig
    """
    return read_dictionary_from_config_directory(
        BUILD_DIR.joinpath("dag"), env, "bi.yml"
    )

def _bi_looker(env: str, generate_code: bool, deploy: bool = False) -> None:
    if generate_code:
        generate_lookML_model(env)

    if deploy:
        deploy_lookML_model(env)

def bi(env: str, generate_code: bool, deploy: bool) -> None:
    bi_config = read_bi_config(env)
 
    if bi_config["target_bi"] == "looker":
        _bi_looker(env, generate_code, deploy)
    else:
        raise NotSuppertedBIError()

@click.command(name="bi", help="Preparing, testing and deploying integrated BI solutions")
@click.option(
    "--env",
    default="local",
    type=str,
    show_default=True,
    required=True,
    help="Name of the environment",
)
@click.option(
    "--generate-code",
    is_flag=True,
    default=False,
    help="Generate BI data (e.g. lookML model for Looker)",
)
@click.option(
    "--deploy",
    is_flag=True,
    default=False,
    help="Deploy to BI",
)
def bi_command(env: str, generate_code: bool, deploy: bool) -> None:
    bi(env, generate_code, deploy)