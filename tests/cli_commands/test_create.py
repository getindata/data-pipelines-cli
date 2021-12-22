import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import yaml
from click.testing import CliRunner

from data_pipelines_cli.cli import _cli
from data_pipelines_cli.errors import DataPipelinesError, NoConfigFileError


class CreateCommandTestCase(unittest.TestCase):
    copier_src_path = "source_path"
    copier_dst_path = "destination_path"
    goldens_dir_path = pathlib.Path(__file__).parent.parent.joinpath("goldens")

    def _mock_copier(self, src_path: str, dst_path: str):
        self.assertEqual(self.copier_src_path, src_path)
        self.assertEqual(self.copier_dst_path, dst_path)

    def test_create_no_config(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
            pathlib.Path(tmp_dir).joinpath("non_existing_file"),
        ):
            runner = CliRunner(mix_stderr=False)
            result = runner.invoke(_cli, ["create", "some_path"])
            self.assertEqual(1, result.exit_code)
            self.assertIsInstance(result.exception, NoConfigFileError)

    @patch(
        "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
        goldens_dir_path.joinpath("example_config.yml"),
    )
    def test_create_with_template_path(self):
        with patch("copier.copy", self._mock_copier):
            runner = CliRunner(mix_stderr=False)
            result = runner.invoke(
                _cli, ["create", self.copier_dst_path, self.copier_src_path]
            )
            self.assertEqual(0, result.exit_code, msg=result.exception)

    @patch(
        "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
        goldens_dir_path.joinpath("example_config.yml"),
    )
    def test_create_with_template_name(self):
        with patch("copier.copy", self._mock_copier):
            runner = CliRunner(mix_stderr=False)
            result = runner.invoke(
                _cli, ["create", self.copier_dst_path, "create_test"]
            )
            self.assertEqual(0, result.exit_code, msg=result.exception)

    @patch(
        "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
        goldens_dir_path.joinpath("example_config.yml"),
    )
    @patch("questionary.select")
    def test_create_without_template_path(self, mock_select):
        magic_mock = MagicMock()
        magic_mock.configure_mock(**{"ask": lambda: "create_test"})
        mock_select.return_value = magic_mock

        with patch("copier.copy", self._mock_copier):
            runner = CliRunner(mix_stderr=False)
            result = runner.invoke(_cli, ["create", self.copier_dst_path])
            self.assertEqual(0, result.exit_code, msg=result.exception)

    def test_no_templates(self):
        with tempfile.NamedTemporaryFile() as tmp_file, patch(
            "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
            pathlib.Path(tmp_file.name),
        ):
            with open(tmp_file.name, "w") as f:
                yaml.dump({"vars": {}, "templates": {}}, f)
            runner = CliRunner(mix_stderr=False)
            result = runner.invoke(_cli, ["create", "some_path"])
            self.assertEqual(1, result.exit_code)
            self.assertIsInstance(result.exception, DataPipelinesError)
            self.assertRegex(result.exception.message, r"^No template provided\..*")
