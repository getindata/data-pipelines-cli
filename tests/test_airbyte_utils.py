import copy
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import yaml
from requests import HTTPError

from data_pipelines_cli.airbyte_utils import (
    create_update_connection,
    env_replacer,
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

    @patch("data_pipelines_cli.airbyte_utils.request_handler")
    def test_request_handler(self, mock_run):
        mock_run.side_effect = self.raise_helper
        try:
            request_handler(self.airbyte_url, self.airbyte_config)
        except HTTPError as e:
            self.assertIsInstance(e, HTTPError)

    @staticmethod
    def raise_helper() -> None:
        raise HTTPError

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
