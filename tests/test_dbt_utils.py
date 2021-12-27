import pathlib
import tempfile
import unittest
from typing import List
from unittest.mock import patch

import yaml

from data_pipelines_cli.dbt_utils import _read_dbt_vars_from_configs, run_dbt_command
from data_pipelines_cli.errors import NoConfigFileError


class DbtUtilsTest(unittest.TestCase):
    dp_config = {
        "vars": {
            "var1": 1,
            "var2": "var2_value",
        },
        "templates": {},
    }
    dbt_config = {
        "target": "env_execution",
        "target_type": "bigquery",
    }
    goldens_dir_path = pathlib.Path(__file__).parent.joinpath("goldens")

    def setUp(self) -> None:
        self.subprocess_run_args = []

    def _mock_run(self, args: List[str]):
        self.subprocess_run_args = args

    def test_dbt_run(self):
        with tempfile.NamedTemporaryFile() as tmp_file, patch(
            "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
            pathlib.Path(tmp_file.name),
        ), patch(
            "data_pipelines_cli.dbt_utils.read_dictionary_from_config_directory",
            lambda _a, _b, _c: self.dbt_config,
        ), patch(
            "data_pipelines_cli.dbt_utils.subprocess_run", self._mock_run
        ):
            with open(tmp_file.name, "w") as f:
                yaml.dump(self.dp_config, f)
            run_dbt_command(
                ("really", "long", "command"), "test_env", pathlib.Path("profiles_path")
            )
            self.assertListEqual(
                [
                    "dbt",
                    "really",
                    "long",
                    "command",
                    "--profile",
                    "bigquery",
                    "--profiles-dir",
                    "profiles_path",
                    "--target",
                    "env_execution",
                    "--vars",
                    "{var1: 1, var2: var2_value}\n",
                ],
                self.subprocess_run_args,
            )

    def test_read_vars_no_throw(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
            pathlib.Path(tmp_dir).joinpath("non_existing_config_file"),
        ):
            try:
                result = _read_dbt_vars_from_configs({})
                self.assertEqual("{}", result.rstrip())
            except NoConfigFileError:
                self.fail("_read_dbt_vars_from_configs() raised NoConfigFileError!")
