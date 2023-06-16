import ast
import copy
import json
import os
import pathlib
from typing import Any, Dict, Optional, Union

import requests
import yaml

from .cli_constants import BUILD_DIR
from .cli_utils import echo_error, echo_info


class AirbyteFactory:
    """A class used to create and update Airbyte connections defined in config yaml file"""

    airbyte_config_path: pathlib.Path
    """Path to config yaml file containing connections definitions"""
    auth_token: Optional[str]
    """Authorization OIDC ID token for a service account to communication with Airbyte instance"""
    connections: Dict[str, Any]
    """List of workspace connections"""
    sources: Dict[str, Any]
    """List of workspace sources"""
    destinations: Dict[str, Any]
    """List of workspace destinations"""

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

    def get_connections(self) -> None:
        """List all Airbyte connections from a workspace"""
        response_search = self.request_handler(
            "connections/list",
            data={"workspaceId": self.get_workspace_id()}
        )
        self.connections = response_search["connections"]
        # TODO: optionally add workspace and connections collection as a parameter

    def get_sources(self) -> None:
        """List all Airbyte sources from a workspace"""
        response_search = self.request_handler(
            "sources/list",
            data={"workspaceId": self.get_workspace_id()}
        )
        self.sources = response_search["sources"]
        # TODO: optionally add workspace and sources collection as a parameter

    def get_destinations(self) -> None:
        """List all Airbyte destinations from a workspace"""
        response_search = self.request_handler(
            "destinations/list",
            data={"workspaceId": self.get_workspace_id()}
        )
        self.sources = response_search["sources"]
        # TODO: optionally add workspace and destinations collection as a parameter

    def persist_airbyte_config(self) -> None:
        """Save all the sources, destination and connections into a config file"""
        pass

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
            "connections/search",
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
                "connections/create",
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
                "connections/update",
                connection_config_copy,
            )
            os.environ[response_update["name"]] = response_update["connectionId"]

    def update_file(self, updated_config: Dict[str, Any]) -> None:
        with open(self.airbyte_config_path, "w") as airbyte_config_file:
            yaml.safe_dump(updated_config, airbyte_config_file)

    def request_handler(self, endpoint: str, config: Dict[str, Any]) -> Union[Dict[str, Any], Any]:
        url = f"{self.airbyte_url}/api/v1/{endpoint}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.auth_token is not None:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        try:
            response = requests.post(url=url, headers=headers, data=json.dumps(config))
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.HTTPError as e:
            echo_error(e.response.text)
            return None
