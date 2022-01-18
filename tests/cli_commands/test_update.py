import unittest
from unittest.mock import patch

from click.testing import CliRunner

from data_pipelines_cli.cli import _cli
from data_pipelines_cli.cli_commands import update
from data_pipelines_cli.errors import NotAProjectDirectoryError


class UpdateCommandTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.dst_path = None
        self.vcs_ref = ""
        self.copier_force = True

    def _mock_copier(self, dst_path: str, vcs_ref: str, force: bool):
        self.dst_path = dst_path
        self.vcs_ref = vcs_ref
        self.force = force

    def test_update_with_dst_path(self):
        with patch("copier.copy", self._mock_copier):
            runner = CliRunner(mix_stderr=False)
            result = runner.invoke(_cli, ["update", "/some_path/", "/other_path/"])
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual("HEAD", self.vcs_ref)
            self.assertEqual(True, self.force)
            self.assertEqual("/some_path/", self.dst_path)

    def test_update_with_dst_path_and_vcs_ref(self):
        with patch("copier.copy", self._mock_copier):
            runner = CliRunner(mix_stderr=False)
            result = runner.invoke(
                _cli,
                [
                    "update",
                    "/some_path/",
                    "--vcs-ref",
                    "2514ef4ca5929e0f5e7a2b9c702a4cd58a6d2ecf",
                ],
            )
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual("2514ef4ca5929e0f5e7a2b9c702a4cd58a6d2ecf", self.vcs_ref)
            self.assertEqual(True, self.force)
            self.assertEqual("/some_path/", self.dst_path)

    def test_update_no_copier_answers(self):
        with self.assertRaises(NotAProjectDirectoryError):
            update.update("not_existing_path", "HEAD")
