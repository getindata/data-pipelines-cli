import copy
import os
import pathlib
import tempfile
import unittest
from unittest.mock import Mock, call, patch

import yaml
from requests import HTTPError

from data_pipelines_cli.airbyte_utils import AirbyteFactory


def read_file(file_path: pathlib.Path):
    with open(file_path, "r") as airbyte_config_file:
        airbyte_config = yaml.safe_load(airbyte_config_file)
    return airbyte_config


class AirbyteUtilsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.airbyte_file = pathlib.Path(__file__).parent.joinpath(
            "goldens/config/airbyte/airbyte.yml"
        )
        self.airbyte_config = read_file(self.airbyte_file)
        self.airbyte_url = self.airbyte_config["airbyte_url"]
        self.auth_token = "7bnjf820ds02d8fhjbn3720b4jk4"
        self.test_airbyte_factory = AirbyteFactory(self.airbyte_file, self.auth_token)

    def test_find_config_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.airbyte_utils.BUILD_DIR", pathlib.Path(tmp_dir)
        ):
            self.assertEqual(
                AirbyteFactory.find_config_file("some_nonexistent_env", "some_file_name"),
                pathlib.Path(tmp_dir) / "dag" / "config" / "base" / "some_file_name.yml",
            )

        env_name, config_name = "some_env", "some_config_name"
        with tempfile.TemporaryDirectory(prefix="asssd") as tmp_dir, patch(
            "data_pipelines_cli.airbyte_utils.BUILD_DIR", pathlib.Path(tmp_dir)
        ):
            configpath = pathlib.Path(tmp_dir).joinpath("dag", "config", env_name)
            configpath.mkdir(parents=True)
            configpath.joinpath(f"{config_name}.yml").touch()
            self.assertEqual(
                AirbyteFactory.find_config_file(env_name, config_name),
                pathlib.Path(tmp_dir) / "dag" / "config" / env_name / f"{config_name}.yml",
            )

    @patch.dict(os.environ, {"CONNECTION_1_ID": "CONN-1-ID", "CONNECTION_2_ID": "CONN-2-ID"})
    @patch("data_pipelines_cli.airbyte_utils.AirbyteFactory.create_update_connection")
    def test_create_update_connections(self, mock_create_update_connection):
        mock_create_update_connection.return_value = None

        connection_1_config = {"name": "connection_1_name"}
        connection_2_config = {"name": "connection_2_name"}
        task_1_config = {"api_version": "v1", "connection_id": "${CONNECTION_1_ID}"}
        task_2_config = {"api_version": "v2", "connection_id": "${CONNECTION_2_ID}"}
        workspace_id = "35ac8060-b4da-4742-b5ba-16ce29dcf526"
        config = {
            "airbyte_url": self.airbyte_url,
            "workspace_id": workspace_id,
            "connections": {
                "connection_1": connection_1_config,
                "connection_2": connection_2_config,
            },
            "tasks": [task_1_config, task_2_config],
        }
        with tempfile.NamedTemporaryFile(mode="w") as tmp_file:
            with open(tmp_file.name, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            AirbyteFactory(pathlib.Path(tmp_file.name), None).create_update_connections()
            mock_create_update_connection.assert_has_calls(
                [
                    call(connection_config=connection_1_config, workspace_id=workspace_id),
                    call(connection_config=connection_2_config, workspace_id=workspace_id),
                ]
            )
            with open(tmp_file.name, "r") as f:
                updated_config = yaml.safe_load(f.read())
            self.assertEqual(updated_config["tasks"][0]["connection_id"], "CONN-1-ID")
            self.assertEqual(updated_config["tasks"][1]["connection_id"], "CONN-2-ID")

    def test_env_replacer(self):
        os.environ["POSTGRES_BQ_CONNECTION"] = "123"
        input = {"connection_id": "${POSTGRES_BQ_CONNECTION}"}
        valid_output = {"connection_id": "123"}
        test_output = AirbyteFactory.env_replacer(input)
        self.assertDictEqual(valid_output, test_output)

    def test_update_file(self):
        config = copy.deepcopy(self.airbyte_config)
        config["tasks"][0]["connectionId"] = 123
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(pathlib.Path(tmp_dir).joinpath("airbyte.yml"), "w") as airbyte_file:
                yaml.safe_dump(config, airbyte_file)

            airbyte_config_path = pathlib.Path(tmp_dir).joinpath("airbyte.yml")
            AirbyteFactory(airbyte_config_path, None).update_file(
                config,
            )
            with open(airbyte_config_path, "r") as airbyte_file:
                airbyte_config = yaml.safe_load(airbyte_file)
                self.assertDictEqual(config, airbyte_config)

    @patch("data_pipelines_cli.airbyte_utils.echo_error")
    @patch("requests.post")
    def test_request_handler(
        self,
        mock_post,
        mock_echo,
    ):
        mock_post.side_effect = [
            Mock(status_code=200, json=lambda: {"data": {"id": "test"}}),
            Mock(status_code=404, raise_for_status=self.raise_helper()),
        ]

        self.assertTrue(
            self.test_airbyte_factory.request_handler("connections/search", self.airbyte_config),
            {"data": {"id": "test"}},
        )
        self.assertIsNone(
            self.test_airbyte_factory.request_handler("connections/update", self.airbyte_config)
        )
        mock_echo.assert_called_with("Not Found")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}",
        }
        mock_post.assert_has_calls(
            [
                call(
                    url=f"{self.airbyte_url}/api/v1/connections/search",
                    headers=headers,
                    json=self.airbyte_config,
                ),
                call(
                    url=f"{self.airbyte_url}/api/v1/connections/update",
                    headers=headers,
                    json=self.airbyte_config,
                ),
            ],
            any_order=True,
        )

    @staticmethod
    def raise_helper() -> Mock:
        exception = HTTPError()
        exception.response = Mock(text="Not Found")
        return Mock(side_effect=exception)

    @patch("data_pipelines_cli.airbyte_utils.AirbyteFactory.request_handler")
    def test_create_connection(self, mock_request_handler):
        mock_request_handler.side_effect = [
            {"connections": []},
            {
                "name": "POSTGRES_BQ_CONNECTION",
                "connectionId": "7aa68945-3e4b-4e1c-b504-2c36e5be2952",
            },
        ]
        # TODO
        self.test_airbyte_factory.create_update_connection(
            connection_config=self.airbyte_config["connections"]["POSTGRES_BQ_CONNECTION"],
            workspace_id=self.airbyte_config["workspace_id"],
        )

        endpoint = mock_request_handler.call_args[0][0]
        self.assertEqual("connections/create", endpoint)

        self.assertEqual(
            os.environ["POSTGRES_BQ_CONNECTION"], "7aa68945-3e4b-4e1c-b504-2c36e5be2952"
        )

    @patch("data_pipelines_cli.airbyte_utils.AirbyteFactory.request_handler")
    def test_update_connection(self, mock_run):
        mock_run.side_effect = [
            {
                "connections": [
                    {
                        "connectionId": "7aa68945-3e4b-4e1c-b504-2c36e5be2952",
                        "sourceId": "06a6f19f-b747-4672-a191-80b96f67c36e",
                        "destinationId": "b3696ac3-93b2-4039-9021-e1f884b03a95",
                        "namespaceFormat": "jaffle_shop",
                        "namespaceDefinition": "customformat",
                    }
                ]
            },
            {
                "name": "POSTGRES_BQ_CONNECTION",
                "connectionId": "7aa68945-3e4b-4e1c-b504-2c36e5be2952",
                "sourceId": "d96241c6-f3af-4736-bd51-dcfce0f68f28",
                "destinationId": "ae11b31a-3e4f-432b-b6f4-967a79535270",
            },
        ]
        self.test_airbyte_factory.create_update_connection(
            connection_config=self.airbyte_config["connections"]["POSTGRES_BQ_CONNECTION"],
            workspace_id=self.airbyte_config.get("workspace_id"),
        )

        endpoint = mock_run.call_args[0][0]
        self.assertEqual("connections/update", endpoint)

        self.assertEqual(
            os.environ["POSTGRES_BQ_CONNECTION"], "7aa68945-3e4b-4e1c-b504-2c36e5be2952"
        )
