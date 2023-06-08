import ast
import copy
import os
import pathlib
from typing import Any, Dict, Iterable, Optional, Union

import requests
import yaml

from .cli_constants import BUILD_DIR
from .cli_utils import echo_error, echo_info


class AirbyteError(Exception):
    pass


class AirbyteConfigMissingWorkspaceIdError(AirbyteError):
    pass


class AirbyteFactory:
    """A class used to create and update Airbyte connections defined in config yaml file"""

    airbyte_config_path: pathlib.Path
    """Path to config yaml file containing connections definitions"""
    auth_token: Optional[str]
    """Authorization OIDC ID token for a service account to communication with Airbyte instance"""

    def __init__(self, airbyte_config_path: pathlib.Path, auth_token: Optional[str]) -> None:
        self.airbyte_config_path = airbyte_config_path
        self.auth_token = auth_token

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
        if not self.airbyte_config["connections"]:
            return

        if not (workspace_id := self.airbyte_config.get("workspace_id")):
            raise AirbyteConfigMissingWorkspaceIdError(
                "Property workspace_id not found in Airbyte config."
            )

        for connection in self.airbyte_config["connections"]:
            self.create_update_connection(
                connection_config=self.airbyte_config["connections"][connection],
                workspace_id=workspace_id,
            )

        for task in self.airbyte_config["tasks"]:
            task.update(self.env_replacer(task))

        self.update_file(self.airbyte_config)

    def create_update_connection(self, connection_config: Dict[str, Any], workspace_id: str) -> Any:
        def configs_equal(
            conf_a: Dict[str, Any], conf_b: Dict[str, Any], equality_fields: Iterable[str]
        ) -> bool:
            conn_a = {k: v for k, v in conf_a.items() if k in equality_fields}
            conn_b = {k: v for k, v in conf_b.items() if k in equality_fields}
            return conn_a == conn_b

        connection_config_copy = copy.deepcopy(connection_config)

        response_search = self.request_handler(
            "connections/list", data={"workspaceId": workspace_id}
        )

        equality_fields = [
            "sourceId",
            "destinationId",
            "namespaceDefinition",
            "namespaceFormat",
        ]

        matching_connections = [
            connection
            for connection in response_search["connections"]
            if configs_equal(connection_config_copy, connection, equality_fields)
        ]

        if not matching_connections:
            echo_info(f"Creating connection config for {connection_config_copy['name']}")
            response_create = self.request_handler(
                "connections/create",
                connection_config_copy,
            )
            os.environ[response_create["name"]] = response_create["connectionId"]
            return

        echo_info(f"Updating connection config for {connection_config_copy['name']}")
        connection_config_copy.pop("sourceId", None)
        connection_config_copy.pop("destinationId", None)
        connection_config_copy["connectionId"] = response_search["connections"][0]["connectionId"]
        response_update = self.request_handler(
            "connections/update",
            connection_config_copy,
        )
        os.environ[response_update["name"]] = response_update["connectionId"]

    def update_file(self, updated_config: Dict[str, Any]) -> None:
        with open(self.airbyte_config_path, "w") as airbyte_config_file:
            yaml.safe_dump(updated_config, airbyte_config_file)

    def request_handler(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], Any]:
        url = f"{self.airbyte_url}/api/v1/{endpoint}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.auth_token is not None:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            response = requests.post(url=url, headers=headers, json=data)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.HTTPError as e:
            echo_error(e.response.text)
            return None
