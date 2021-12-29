import pathlib
import tempfile
import unittest
from unittest.mock import patch

import yaml
from click.testing import CliRunner

from data_pipelines_cli.cli import _cli
from data_pipelines_cli.cli_commands.prepare_env import prepare_env
from data_pipelines_cli.errors import JinjaVarKeyError


class GenHomeProfilesCommandTestCase(unittest.TestCase):
    goldens_dir_path = pathlib.Path(__file__).parent.parent.joinpath("goldens")
    rendered_from_vars_profile = {
        "bigquery": {
            "target": "env_execution",
            "outputs": {
                "env_execution": {
                    "method": "service-account",
                    "project": "example-project",
                    "dataset": "var21-dataset",
                    "keyfile": "/tmp/a/b/c/d.json",
                    "timeout_seconds": 150,
                    "priority": "interactive",
                    "location": "us-west1",
                    "threads": 1337,
                    "retries": 1,
                    "type": "bigquery",
                }
            },
        }
    }

    def setUp(self) -> None:
        self.maxDiff = None

    def test_no_var_profiles_generation(self):
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_constants.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.config_generation.BUILD_DIR",
            pathlib.Path(tmp_dir),
        ), patch(
            "data_pipelines_cli.dbt_utils.BUILD_DIR",
            pathlib.Path(tmp_dir),
        ), patch(
            "pathlib.Path.cwd", lambda: self.goldens_dir_path
        ), tempfile.TemporaryDirectory() as tmp_dir2, patch(
            "pathlib.Path.home", lambda: pathlib.Path(tmp_dir2)
        ):
            runner.invoke(_cli, ["prepare-env"])
            with open(
                pathlib.Path(tmp_dir2).joinpath(".dbt", "profiles.yml"), "r"
            ) as generated, open(
                self.goldens_dir_path.joinpath(
                    "example_profiles", "local_snowflake.yml"
                ),
                "r",
            ) as prepared:
                self.assertDictEqual(
                    yaml.safe_load(prepared), yaml.safe_load(generated)
                )

    def test_vars_profiles_generation(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_constants.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.config_generation.BUILD_DIR",
            pathlib.Path(tmp_dir),
        ), patch(
            "data_pipelines_cli.dbt_utils.BUILD_DIR",
            pathlib.Path(tmp_dir),
        ), patch.dict(
            "os.environ", BIGQUERY_KEYFILE="/tmp/a/b/c/d.json"
        ), patch(
            "pathlib.Path.cwd", lambda: self.goldens_dir_path
        ), tempfile.TemporaryDirectory() as tmp_dir2, patch(
            "pathlib.Path.home", lambda: pathlib.Path(tmp_dir2)
        ):
            prepare_env("staging")

            with open(
                pathlib.Path(tmp_dir2).joinpath(".dbt", "profiles.yml"), "r"
            ) as generated:
                self.assertDictEqual(
                    self.rendered_from_vars_profile, yaml.safe_load(generated)
                )

    def test_raise_missing_variable(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_constants.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.config_generation.BUILD_DIR",
            pathlib.Path(tmp_dir),
        ), patch(
            "data_pipelines_cli.cli_commands.prepare_env.read_dbt_vars_from_configs",
            lambda _env: {},
        ), patch.dict(
            "os.environ", BIGQUERY_KEYFILE="/tmp/a/b/c/d.json"
        ), patch(
            "pathlib.Path.cwd", lambda: self.goldens_dir_path
        ), tempfile.TemporaryDirectory() as tmp_dir2, patch(
            "pathlib.Path.home", lambda: pathlib.Path(tmp_dir2)
        ):
            with self.assertRaises(JinjaVarKeyError):
                prepare_env("staging")

    def test_raise_missing_environment_variable(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_constants.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.config_generation.BUILD_DIR",
            pathlib.Path(tmp_dir),
        ), patch(
            "data_pipelines_cli.dbt_utils.BUILD_DIR",
            pathlib.Path(tmp_dir),
        ), patch.dict(
            "os.environ", {}
        ), patch(
            "pathlib.Path.cwd", lambda: self.goldens_dir_path
        ), tempfile.TemporaryDirectory() as tmp_dir2, patch(
            "pathlib.Path.home", lambda: pathlib.Path(tmp_dir2)
        ):
            with self.assertRaises(JinjaVarKeyError):
                prepare_env("staging")
