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
from .errors import AirbyteFactoryError


class AirbyteFactory:
    """A class used to create and update Airbyte connections defined in config yaml file"""

    airbyte_config_path: pathlib.Path
    """Path to config yaml file containing connections definitions"""
    iap_enabled: bool
    """Whether Airbyte instance is secured with IAP"""
    airbyte_iap_client_id: Optional[str]
    """IAP Client ID of Airbyte instance"""
    gcp_sa_key_path: Optional[str]
    """Path to the key file of GCP service account for communication with IAP"""
    """"""

    def __init__(
        self,
        airbyte_config_path: pathlib.Path,
        iap_enabled: bool,
        airbyte_iap_client_id: Optional[str] = None,
        gcp_sa_key_path: Optional[str] = None,
    ) -> None:
        self.airbyte_config_path = airbyte_config_path
        self.iap_enabled = iap_enabled
        self.airbyte_iap_client_id = airbyte_iap_client_id
        self.gcp_sa_key_path = gcp_sa_key_path

        if self.iap_enabled and (
            self.airbyte_iap_client_id is None or self.gcp_sa_key_path is None
        ):
            missing_attributes = ["Missing information to authorize IAP request."]
            if self.airbyte_iap_client_id is None:
                missing_attributes.append(
                    "Make sure that argument `--airbyte-iap-client-id` is supplied to the dp command."
                )
            if self.gcp_sa_key_path is None:
                missing_attributes.append(
                    "Make sure that argument `--gcp-sa-key-path` is supplied to the dp command."
                )
            raise AirbyteFactoryError(
                "\n".join(
                    missing_attributes,
                )
            )

        with open(self.airbyte_config_path, "r") as airbyte_config_file:
            self.airbyte_config = yaml.safe_load(airbyte_config_file)
        self.airbyte_url = self.airbyte_config["airbyte_url"]

    @staticmethod
    def find_config_file(env: str, config_name: str = "airbyte") -> pathlib.Path:
        if BUILD_DIR.joinpath("dag", "config", env, f"{config_name}.yml").is_file():
            return BUILD_DIR.joinpath("dag", "config", env, f"{config_name}.yml")
        return BUILD_DIR.joinpath("dag", "config", "base", f"{config_name}.yml")

    @staticmethod
    def env_replacer(config: Dict[str, Any]) -> Dict[str, Any]:
        return ast.literal_eval(os.path.expandvars(f"{config}"))

    def create_update_connections(self) -> None:
        """Create and update Airbyte connections defined in config yaml file"""
        if self.airbyte_config["connections"]:
            [
                self.create_update_connection(self.airbyte_config["connections"][connection])
                for connection in self.airbyte_config["connections"]
            ]
            [task.update(self.env_replacer(task)) for task in self.airbyte_config["tasks"]]
            self.update_file(self.airbyte_config)

    def create_update_connection(self, connection_config: Dict[str, Any]) -> Any:
        connection_config_copy = copy.deepcopy(connection_config)
        response_search = self.request_handler(
            f"{self.airbyte_url}/api/v1/connections/search",
            {
                "sourceId": connection_config_copy["sourceId"],
                "destinationId": connection_config_copy["destinationId"],
                "namespaceDefinition": connection_config_copy["namespaceDefinition"],
                "namespaceFormat": connection_config_copy["namespaceFormat"],
            },
        )
        if not response_search["connections"]:
            echo_info(f"Creating connection config for {connection_config_copy['name']}")
            response_create = self.request_handler(
                f"{self.airbyte_url}/api/v1/connections/create",
                connection_config_copy,
            )
            os.environ[response_create["name"]] = response_create["connectionId"]
        else:
            echo_info(f"Updating connection config for {connection_config_copy['name']}")
            connection_config_copy.pop("sourceId", None)
            connection_config_copy.pop("destinationId", None)
            connection_config_copy["connectionId"] = response_search["connections"][0][
                "connectionId"
            ]
            response_update = self.request_handler(
                f"{self.airbyte_url}/api/v1/connections/update",
                connection_config_copy,
            )
            os.environ[response_update["name"]] = response_update["connectionId"]

    def update_file(self, updated_config: Dict[str, Any]) -> None:
        with open(self.airbyte_config_path, "w") as airbyte_config_file:
            yaml.safe_dump(updated_config, airbyte_config_file)

    def request_handler(self, url: str, config: Dict[str, Any]) -> Union[Dict[str, Any], Any]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.iap_enabled:
            idToken = get_idToken_from_service_account_file(
                self.gcp_sa_key_path, self.airbyte_iap_client_id
            )
            headers["Authorization"] = f"Bearer {idToken}"
        try:
            response = requests.post(url=url, headers=headers, data=json.dumps(config))
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.HTTPError as e:
            echo_error(e.response.text)
            return None
