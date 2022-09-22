import click

from ..cli_constants import BUILD_DIR
from ..config_generation import read_dictionary_from_config_directory
from ..looker_utils import generate_lookML_model, deploy_lookML_model
from ..errors import NotSuppertedBIError, DataPipelinesError
from typing import Any, Dict, Optional

def read_bi_config(env: str) -> Dict[str, Any]:
    return read_dictionary_from_config_directory(
        BUILD_DIR.joinpath("dag"), env, "bi.yml"
    )

def _bi_looker(env: str, generate_code: bool, deploy: bool = False, key_path: Optional[str] = None) -> None:
    if generate_code:
        generate_lookML_model()

    if deploy:
        if key_path is None:
            raise DataPipelinesError(
                "Error raised when pushing Looker code. No repository key provided. "
                "Provide key using '--key-path' option"
            )
        deploy_lookML_model(key_path, env)

def bi(env: str, generate_code: bool, deploy: bool = False, key_path: Optional[str] = None) -> None:
    bi_config = read_bi_config(env)
 
    if bi_config["target_bi"] == "looker":
        _bi_looker(env, generate_code, deploy, key_path)
    else:
        raise NotSuppertedBIError()

@click.command(name="bi", help="Generate and push BI codes")
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
@click.option(
    "--key-path",
    type=str,
    required=False,
    help="Path to the key with write access to repo with published BI code",
)
def bi_command(env: str, generate_code: bool, deploy: bool, key_path: str) -> None:
    bi(env, generate_code, deploy, key_path)