import copy
import os
import pathlib
import tempfile
import unittest
from unittest.mock import Mock, call, patch

import yaml
from requests import HTTPError

from data_pipelines_cli.airbyte_utils import (
    create_update_connection,
    env_replacer,
    factory,
    find_config_file,
    request_handler,
    update_file,
)


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

    def test_find_config_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.airbyte_utils.BUILD_DIR", pathlib.Path(tmp_dir)
        ):
            self.assertEqual(
                find_config_file("some_nonexistent_env", "some_file_name"),
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
                find_config_file(env_name, config_name),
                pathlib.Path(tmp_dir) / "dag" / "config" / env_name / f"{config_name}.yml",
            )

    @patch.dict(os.environ, {"CONNECTION_1_ID": "CONN-1-ID", "CONNECTION_2_ID": "CONN-2-ID"})
    @patch("data_pipelines_cli.airbyte_utils.create_update_connection")
    def test_factory(self, mock_create_update_connection):
        mock_create_update_connection.return_value = None
        test_airbyte_url = "http://some-airbyte/url"
        connection_1_config = {"name": "connection_1_name"}
        connection_2_config = {"name": "connection_2_name"}
        task_1_config = {"api_version": "v1", "connection_id": "${CONNECTION_1_ID}"}
        task_2_config = {"api_version": "v2", "connection_id": "${CONNECTION_2_ID}"}
        config = {
            "airbyte_url": test_airbyte_url,
            "connections": {
                "connection_1": connection_1_config,
                "connection_2": connection_2_config,
            },
            "tasks": [task_1_config, task_2_config],
        }
        with tempfile.NamedTemporaryFile(mode="w") as tmp_file:
            with open(tmp_file.name, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            factory(pathlib.Path(tmp_file.name))
            mock_create_update_connection.assert_has_calls(
                [
                    call(connection_1_config, test_airbyte_url),
                    call(connection_2_config, test_airbyte_url),
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
        test_output = env_replacer(input)
        self.assertDictEqual(valid_output, test_output)

    def test_update_file(self):
        config = copy.deepcopy(self.airbyte_config)
        config["tasks"][0]["connectionId"] = 123
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(pathlib.Path(tmp_dir).joinpath("airbyte.yml"), "w") as airbyte_file:
                yaml.safe_dump(config, airbyte_file)

            update_file(config, pathlib.Path(tmp_dir).joinpath("airbyte.yml"))
            with open(pathlib.Path(tmp_dir).joinpath("airbyte.yml"), "r") as airbyte_file:
                airbyte_config = yaml.safe_load(airbyte_file)
                self.assertDictEqual(config, airbyte_config)

    @patch("data_pipelines_cli.airbyte_utils.echo_error")
    @patch("requests.post")
    def test_request_handler(self, mock_post, mock_echo):
        mock_post.side_effect = [
            Mock(status_code=200, json=lambda: {"data": {"id": "test"}}),
            Mock(status_code=404, raise_for_status=self.raise_helper()),
        ]
        self.assertTrue(
            request_handler(self.airbyte_url, self.airbyte_config), {"data": {"id": "test"}}
        )
        res = request_handler(self.airbyte_url, self.airbyte_config)
        mock_echo.assert_called_with("Not Found")
        self.assertIsNone(res)

    @staticmethod
    def raise_helper() -> Mock:
        exception = HTTPError()
        exception.response = Mock(text="Not Found")
        return Mock(side_effect=exception)

    @patch("data_pipelines_cli.airbyte_utils.request_handler")
    def test_create_connection(self, mock_run):
        mock_run.side_effect = [
            {"connections": []},
            {
                "name": "POSTGRES_BQ_CONNECTION",
                "connectionId": "7aa68945-3e4b-4e1c-b504-2c36e5be2952",
            },
        ]
        create_update_connection(
            self.airbyte_config["connections"]["POSTGRES_BQ_CONNECTION"], self.airbyte_url
        )
        self.assertEqual(
            os.environ["POSTGRES_BQ_CONNECTION"], "7aa68945-3e4b-4e1c-b504-2c36e5be2952"
        )

    @patch("data_pipelines_cli.airbyte_utils.request_handler")
    def test_update_connection(self, mock_run):
        mock_run.side_effect = [
            {"connections": [{"connectionId": "7aa68945-3e4b-4e1c-b504-2c36e5be2952"}]},
            {
                "name": "POSTGRES_BQ_CONNECTION",
                "connectionId": "7aa68945-3e4b-4e1c-b504-2c36e5be2952",
                "sourceId": "d96241c6-f3af-4736-bd51-dcfce0f68f28",
                "destinationId": "ae11b31a-3e4f-432b-b6f4-967a79535270",
            },
        ]
        create_update_connection(
            self.airbyte_config["connections"]["POSTGRES_BQ_CONNECTION"], self.airbyte_url
        )
        self.assertEqual(
            os.environ["POSTGRES_BQ_CONNECTION"], "7aa68945-3e4b-4e1c-b504-2c36e5be2952"
        )
