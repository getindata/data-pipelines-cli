import pathlib
import tempfile
import unittest
from typing import List
from unittest.mock import patch

from click.testing import CliRunner

from data_pipelines_cli.cli import _cli


class RunTestCommandTestCase(unittest.TestCase):
    commands_to_test = ["run", "test"]
    goldens_dir_path = pathlib.Path(__file__).parent.parent.joinpath("goldens")

    def setUp(self) -> None:
        self.subprocess_run_args = []

    def _mock_run(self, args: List[str]):
        self.subprocess_run_args = args

    @patch(
        "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
        goldens_dir_path.joinpath("example_config.yml"),
    )
    def test_no_arg(self):
        for cmd in self.commands_to_test:
            with self.subTest(command=cmd), patch(
                "pathlib.Path.cwd", lambda: self.goldens_dir_path
            ), tempfile.TemporaryDirectory() as tmp_dir, patch(
                "data_pipelines_cli.config_generation.BUILD_DIR", pathlib.Path(tmp_dir)
            ), patch(
                "data_pipelines_cli.cli_commands.compile.BUILD_DIR",
                pathlib.Path(tmp_dir),
            ), patch(
                "data_pipelines_cli.dbt_utils.BUILD_DIR", pathlib.Path(tmp_dir)
            ), patch(
                "data_pipelines_cli.cli_constants.BUILD_DIR", pathlib.Path(tmp_dir)
            ), patch(
                "data_pipelines_cli.dbt_utils.subprocess_run", self._mock_run
            ):
                runner = CliRunner()
                result = runner.invoke(_cli, [cmd])
                self.assertEqual(0, result.exit_code, msg=result.exception)

                self.assertEqual("dbt", self.subprocess_run_args[0])
                self.assertEqual(cmd, self.subprocess_run_args[1])
                args_str = " ".join(self.subprocess_run_args)
                self.assertIn("--profile snowflake", args_str)
                self.assertIn("--target local", args_str)

    @patch(
        "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
        goldens_dir_path.joinpath("example_config.yml"),
    )
    def test_dev_arg(self):
        for cmd in self.commands_to_test:
            for env in ["dev", "staging"]:
                with self.subTest(command=cmd, environment=env), patch(
                    "pathlib.Path.cwd", lambda: self.goldens_dir_path
                ), tempfile.TemporaryDirectory() as tmp_dir, patch(
                    "data_pipelines_cli.config_generation.BUILD_DIR",
                    pathlib.Path(tmp_dir),
                ), patch(
                    "data_pipelines_cli.cli_commands.compile.BUILD_DIR",
                    pathlib.Path(tmp_dir),
                ), patch(
                    "data_pipelines_cli.dbt_utils.BUILD_DIR", pathlib.Path(tmp_dir)
                ), patch(
                    "data_pipelines_cli.cli_constants.BUILD_DIR", pathlib.Path(tmp_dir)
                ), patch(
                    "data_pipelines_cli.dbt_utils.subprocess_run", self._mock_run
                ):
                    runner = CliRunner()
                    result = runner.invoke(_cli, [cmd, "--env", env])
                    self.assertEqual(0, result.exit_code, msg=result.exception)

                    self.assertEqual("dbt", self.subprocess_run_args[0])
                    self.assertEqual(cmd, self.subprocess_run_args[1])
                    args_str = " ".join(self.subprocess_run_args)
                    self.assertIn("--profile bigquery", args_str)
                    self.assertIn("--target env_execution", args_str)
