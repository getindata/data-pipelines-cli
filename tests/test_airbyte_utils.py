from unittest.mock import patch
import unittest
from data_pipelines_cli.airbyte_utils import env_replacer
import os

class AirbyteUtilsTest(unittest.TestCase):
    def test_env_replacer(self):
        os.environ['POSTGRES_BQ_CONNECTION'] = "123"
        input = {"connection_id": "${POSTGRES_BQ_CONNECTION}"}
        valid_output = {"connection_id": "123"}
        test_output = env_replacer(input)
        self.assertDictEqual(valid_output, test_output)