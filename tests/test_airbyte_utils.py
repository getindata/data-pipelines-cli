import copy
import json
import os
import pathlib
import tempfile
import unittest
from unittest.mock import Mock, call, patch

import yaml
from requests import HTTPError

from data_pipelines_cli.airbyte_utils import AirbyteFactory
from data_pipelines_cli.errors import AirbyteFactoryError


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
        self.airbyte_iap_client_id = "536234aj-666e350l.apps.googleusercontent.com"
        self.gcp_sa_key_path = "some/sa/keyfile/path.json"
        self.test_airbyte_factory = AirbyteFactory(self.airbyte_file, False)

    def test_init_with_iap_without_required_attributes(self):
        err_general = "Missing information to authorize IAP request to Airbyte."
        err_client_id = "Provide `--airbyte-iap-client-id` argument to the dp command."
        err_key_path = "Provide `--gcp-sa-key-path` argument to the dp command."

        with self.assertRaises(AirbyteFactoryError) as err_airbyte_iap_client_id:
            AirbyteFactory(self.airbyte_file, True, None, self.gcp_sa_key_path)
        self.assertTrue(err_general in str(err_airbyte_iap_client_id.exception))
        self.assertTrue(err_client_id in str(err_airbyte_iap_client_id.exception))
        self.assertTrue(err_key_path not in str(err_airbyte_iap_client_id.exception))

        with self.assertRaises(AirbyteFactoryError) as err_gcp_sa_key_path:
            AirbyteFactory(self.airbyte_file, True, self.airbyte_iap_client_id, None)
        self.assertTrue(err_general in str(err_gcp_sa_key_path.exception))
        self.assertTrue(err_client_id not in str(err_gcp_sa_key_path.exception))
        self.assertTrue(err_key_path in str(err_gcp_sa_key_path.exception))

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
        config = {
            "airbyte_url": self.airbyte_url,
            "connections": {
                "connection_1": connection_1_config,
                "connection_2": connection_2_config,
            },
            "tasks": [task_1_config, task_2_config],
        }
        with tempfile.NamedTemporaryFile(mode="w") as tmp_file:
            with open(tmp_file.name, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            AirbyteFactory(pathlib.Path(tmp_file.name), False).create_update_connections()
            mock_create_update_connection.assert_has_calls(
                [
                    call(connection_1_config),
                    call(connection_2_config),
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
            AirbyteFactory(airbyte_config_path, False).update_file(
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
            self.test_airbyte_factory.request_handler(self.airbyte_url, self.airbyte_config),
            {"data": {"id": "test"}},
        )
        res = self.test_airbyte_factory.request_handler(self.airbyte_url, self.airbyte_config)
        mock_echo.assert_called_with("Not Found")
        self.assertIsNone(res)

    @patch("data_pipelines_cli.airbyte_utils.get_idToken_from_service_account_file")
    @patch("data_pipelines_cli.airbyte_utils.echo_error")
    @patch("requests.post")
    def test_request_handler_with_iap(self, mock_post, mock_echo, mock_get_idToken):
        mock_post.side_effect = [
            Mock(status_code=200, json=lambda: {"data": {"id": "test"}}),
            Mock(status_code=404, raise_for_status=self.raise_helper()),
        ]
        mock_get_idToken.return_value = "7bnjf820ds02d"

        test_airbyte_factory_iap = AirbyteFactory(
            self.airbyte_file, True, self.airbyte_iap_client_id, self.gcp_sa_key_path
        )
        self.assertTrue(
            test_airbyte_factory_iap.request_handler(self.airbyte_url, self.airbyte_config),
            {"data": {"id": "test"}},
        )
        self.assertIsNone(
            test_airbyte_factory_iap.request_handler(self.airbyte_url, self.airbyte_config)
        )
        mock_echo.assert_called_with("Not Found")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer 7bnjf820ds02d",
        }
        mock_post.assert_has_calls(
            [
                call(url=self.airbyte_url, headers=headers, data=json.dumps(self.airbyte_config)),
                call(url=self.airbyte_url, headers=headers, data=json.dumps(self.airbyte_config)),
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
            self.airbyte_config["connections"]["POSTGRES_BQ_CONNECTION"]
        )
        self.assertEqual(
            os.environ["POSTGRES_BQ_CONNECTION"], "7aa68945-3e4b-4e1c-b504-2c36e5be2952"
        )

    @patch("data_pipelines_cli.airbyte_utils.AirbyteFactory.request_handler")
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
        self.test_airbyte_factory.create_update_connection(
            self.airbyte_config["connections"]["POSTGRES_BQ_CONNECTION"]
        )
        self.assertEqual(
            os.environ["POSTGRES_BQ_CONNECTION"], "7aa68945-3e4b-4e1c-b504-2c36e5be2952"
        )
