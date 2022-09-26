from enum import Enum
from typing import Any, Dict, Optional, Tuple

from .cli_constants import BUILD_DIR
from .cli_utils import echo_info
from .config_generation import read_dictionary_from_config_directory
from .errors import DataPipelinesError, NotSuppertedBIError
from .looker_utils import deploy_lookML_model, generate_lookML_model


class BiAction(Enum):
    COMPILE = 1
    DEPLOY = 2


def read_bi_config(env: str) -> Dict[str, Any]:
    """
    Read BI configuration.

    :param env: Name of the environment
    :type env: str
    :return: Compiled dictionary
    :rtype: Dict[str, Any]
    """
    return read_dictionary_from_config_directory(BUILD_DIR.joinpath("dag"), env, "bi.yml")


def _bi_looker(
    env: str, generate_code: bool, deploy: bool = False, key_path: Optional[str] = None
) -> None:
    if generate_code:
        echo_info("Generating Looker codes")
        generate_lookML_model()

    if deploy:
        echo_info("Deploying Looker project")
        if key_path is None:
            raise DataPipelinesError(
                "Error raised when pushing Looker code. No repository key provided. "
                "Provide key using '--bi-git-key-path' option or disable BI in bi.yml"
            )
        deploy_lookML_model(key_path, env)


def bi(env: str, bi_action: BiAction, key_path: Optional[str] = None) -> None:
    """
    Generate and deploy BI codes using dbt compiled data.

    :param env: Name of the environment
    :type env: str
    :param bi_action: Action to be run [COMPILE, DEPLOY]
    :type env: BiAction
    :param key_path: Path to the key with write access to git repository
    :type env: str
    :raises NotSuppertedBIError: Not supported bi in bi.yml configuration
    """
    bi_config = read_bi_config(env)
    if not bi_config["is_bi_enabled"]:
        echo_info("BI is disabled")
        return

    if bi_config["bi_target"] == "looker":
        echo_info("Running BI...")
        compile, deploy = _prepare_bi_parameters(bi_action, bi_config)
        _bi_looker(env, compile, deploy, key_path)
    else:
        raise NotSuppertedBIError()


def _prepare_bi_parameters(bi_action: BiAction, bi_config: Dict[str, Any]) -> Tuple[bool, bool]:
    if bi_action == BiAction.COMPILE:
        return bi_config["is_bi_compile"], False
    elif bi_action == BiAction.DEPLOY:
        return False, bi_config["is_bi_deploy"]
    else:
        return False, False
