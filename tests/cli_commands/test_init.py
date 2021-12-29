import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import yaml
from click.testing import CliRunner

from data_pipelines_cli.cli import _cli
from data_pipelines_cli.cli_commands.init import init
from data_pipelines_cli.cli_constants import DEFAULT_GLOBAL_CONFIG
from data_pipelines_cli.data_structures import (
    DataPipelinesConfig,
    TemplateConfig,
    read_config,
)
from data_pipelines_cli.errors import DataPipelinesError


class InitCommandTestCase(unittest.TestCase):
    test_config_template_path = pathlib.Path(__file__).parent.parent.joinpath(
        "goldens", "config_template"
    )
    example_config_dict = DataPipelinesConfig(
        templates={
            "my-template": TemplateConfig(
                template_name="my-template",
                template_path="https://example.com/git/example.git",
            ),
            "local-template": TemplateConfig(
                template_name="local-template",
                template_path="/var/tmp/Documents/project-template",
            ),
        },
        vars={
            "username": "test_user",
        },
    )

    def test_init(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_commands.init.CONFIGURATION_PATH",
            pathlib.Path(tmp_dir).joinpath(".dp.yml"),
        ), patch(
            "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
            pathlib.Path(tmp_dir).joinpath(".dp.yml"),
        ):
            result = runner.invoke(
                _cli,
                ["init", str(self.test_config_template_path)],
                input="test_user\n/var/tmp",
            )
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(self.example_config_dict, read_config())

    def test_global_config(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_commands.init.CONFIGURATION_PATH",
            pathlib.Path(tmp_dir).joinpath(".dp.yml"),
        ), patch(
            "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
            pathlib.Path(tmp_dir).joinpath(".dp.yml"),
        ):
            result = runner.invoke(_cli, ["init"])
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(DEFAULT_GLOBAL_CONFIG, read_config())

    @patch("questionary.confirm")
    def test_overwrite_yes(self, mock_questionary):
        magic_mock = MagicMock()
        magic_mock.configure_mock(**{"ask": lambda: True})
        mock_questionary.return_value = magic_mock

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dp_path = pathlib.Path(tmp_dir).joinpath(".dp.yml")
            with patch(
                "data_pipelines_cli.cli_commands.init.CONFIGURATION_PATH",
                tmp_dp_path,
            ), patch(
                "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
                tmp_dp_path,
            ):
                with open(tmp_dp_path, "w") as tmp_file:
                    yaml.dump(self.example_config_dict, tmp_file)
                    self.assertEqual(self.example_config_dict, read_config())
                init(None)
                self.assertEqual(DEFAULT_GLOBAL_CONFIG, read_config())

    @patch("questionary.confirm")
    def test_overwrite_no(self, mock_questionary):
        magic_mock = MagicMock()
        magic_mock.configure_mock(**{"ask": lambda: False})
        mock_questionary.return_value = magic_mock

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dp_path = pathlib.Path(tmp_dir).joinpath(".dp.yml")
            with patch(
                "data_pipelines_cli.cli_commands.init.CONFIGURATION_PATH",
                tmp_dp_path,
            ), patch(
                "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
                tmp_dp_path,
            ):
                with open(tmp_dp_path, "w") as tmp_file:
                    yaml.dump(self.example_config_dict, tmp_file)
                    self.assertEqual(self.example_config_dict, read_config())

                with self.assertRaises(DataPipelinesError):
                    init(None)
                self.assertEqual(self.example_config_dict, read_config())
