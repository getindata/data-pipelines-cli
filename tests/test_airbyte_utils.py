import copy
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import yaml
from requests import HTTPError

from data_pipelines_cli.airbyte_utils import env_replacer, request_handler, update_file


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
