import ast
import copy
import json
import os
import pathlib
from typing import Any, Dict, Optional, Union

import requests
import yaml

from .cli_constants import BUILD_DIR
from .cli_utils import echo_error, echo_info, get_idToken_from_service_account_file
from .errors import DataPipelinesError


def find_config_file(env: str, config_name: str) -> pathlib.Path:
    if BUILD_DIR.joinpath("dag", "config", env, f"{config_name}.yml").is_file():
        return BUILD_DIR.joinpath("dag", "config", env, f"{config_name}.yml")
    return BUILD_DIR.joinpath("dag", "config", "base", f"{config_name}.yml")


def factory(airbyte_config_path: pathlib.Path, gcp_sa_key_path: Optional[str] = None) -> None:
    with open(airbyte_config_path, "r") as airbyte_config_file:
        airbyte_config = yaml.safe_load(airbyte_config_file)
    airbyte_url = airbyte_config["airbyte_url"]
    if airbyte_config["connections"]:
        [
            create_update_connection(
                airbyte_config["connections"][connection], airbyte_url, gcp_sa_key_path
            )
            for connection in airbyte_config["connections"]
        ]
        [task.update(env_replacer(task)) for task in airbyte_config["tasks"]]
        update_file(airbyte_config, airbyte_config_path)


def update_file(updated_config: Dict[str, Any], airbyte_config_path: pathlib.Path) -> None:
    with open(airbyte_config_path, "w") as airbyte_config_file:
        yaml.safe_dump(updated_config, airbyte_config_file)


def env_replacer(config: Dict[str, Any]) -> Dict[str, Any]:
    return ast.literal_eval(os.path.expandvars(f"{config}"))


def request_handler(
    airbyte_api_url: str, config: Dict[str, Any], gcp_sa_key_path: Optional[str] = None
) -> Union[Dict[str, Any], Any]:
    if gcp_sa_key_path is None:
        raise DataPipelinesError(
            "Could not authorize IAP request. Make sure that argument `--gcp-sa-key-path` is supplied to the command"
        )
    idToken = get_idToken_from_service_account_file(gcp_sa_key_path, airbyte_api_url)
    headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {idToken}",
        }
    try:
        response = requests.post(url=airbyte_api_url, headers=headers, data=json.dumps(config))
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as e:
        echo_error(e.response.text)
        return None


def create_update_connection(
    connection_config: Dict[str, Any], airbyte_url: str, gcp_sa_key_path: Optional[str] = None
) -> Any:
    connection_config_copy = copy.deepcopy(connection_config)
    response_search = request_handler(
        f"{airbyte_url}/api/v1/web_backend/connections/search",
        {
            "sourceId": connection_config_copy["sourceId"],
            "destinationId": connection_config_copy["destinationId"],
            "namespaceDefinition": connection_config_copy["namespaceDefinition"],
            "namespaceFormat": connection_config_copy["namespaceFormat"],
        },
        gcp_sa_key_path,
    )
    if not response_search["connections"]:
        echo_info(f"Creating connection config for {connection_config_copy['name']}")
        response_create = request_handler(
            f"{airbyte_url}/api/v1/web_backend/connections/create",
            connection_config_copy,
            gcp_sa_key_path,
        )
        os.environ[response_create["name"]] = response_create["connectionId"]
    else:
        echo_info(f"Updating connection config for {connection_config_copy['name']}")
        connection_config_copy.pop("sourceId", None)
        connection_config_copy.pop("destinationId", None)
        connection_config_copy["connectionId"] = response_search["connections"][0]["connectionId"]
        response_update = request_handler(
            f"{airbyte_url}/api/v1/web_backend/connections/update",
            connection_config_copy,
            gcp_sa_key_path,
        )
        os.environ[response_update["name"]] = response_update["connectionId"]
