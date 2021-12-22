import pathlib
import tempfile
import unittest
from typing import List
from unittest.mock import patch

from click.testing import CliRunner

from data_pipelines_cli.cli import _cli


class CleanCommandTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.subprocess_run_args = []

    def _mock_run(self, args: List[str]):
        self.subprocess_run_args = args

    def test_clean(self):
        with patch(
            "data_pipelines_cli.cli_commands.clean.subprocess_run", self._mock_run
        ):
            runner = CliRunner()
            result = runner.invoke(_cli, ["clean"])
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertListEqual(["dbt", "clean"], self.subprocess_run_args)

    def test_clean_remove_dir(self):
        with patch(
            "data_pipelines_cli.cli_commands.clean.subprocess_run", self._mock_run
        ), tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_commands.clean.BUILD_DIR", pathlib.Path(tmp_dir)
        ):
            assert pathlib.Path(tmp_dir).exists()
            runner = CliRunner()
            result = runner.invoke(_cli, ["clean"])
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertListEqual(["dbt", "clean"], self.subprocess_run_args)
            assert not pathlib.Path(tmp_dir).exists()

            # Fix for Python 3.7.
            # Otherwise it throws, as there is no directory to remove.
            pathlib.Path(tmp_dir).mkdir(parents=True, exist_ok=True)
