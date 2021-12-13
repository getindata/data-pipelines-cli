import pathlib
import tempfile
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from data_pipelines_cli.cli_commands.init import init_command
from data_pipelines_cli.cli_commands.template import list_templates_command
from data_pipelines_cli.cli_constants import DEFAULT_GLOBAL_CONFIG
from data_pipelines_cli.data_structures import (
    DataPipelinesConfig,
    TemplateConfig,
    read_config_or_exit,
)


class ConfigTestCase(unittest.TestCase):
    example_config_dict = DataPipelinesConfig(
        username="testuser",
        templates={
            "template1": TemplateConfig(
                template_name="template1",
                template_path="https://example.com/xyz/abcd.git",
            ),
            "template2": TemplateConfig(
                template_name="template2",
                template_path="https://example.com/git/example.git",
            ),
        },
    )
    example_config_path = pathlib.Path(__file__).parent.joinpath("example_config.yml")

    def test_read_config(self):
        with patch(
            "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
            self.example_config_path,
        ):
            self.assertEqual(self.example_config_dict, read_config_or_exit())

    def test_list_templates(self):
        runner = CliRunner()
        with patch(
            "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
            self.example_config_path,
        ):
            result = runner.invoke(list_templates_command)
            self.assertEqual(0, result.exit_code)
            self.assertEqual(
                "AVAILABLE TEMPLATES:\n\n"
                "template_name: template1\n"
                "template_path: https://example.com/xyz/abcd.git\n\n"
                "template_name: template2\n"
                "template_path: https://example.com/git/example.git\n\n",
                result.output,
            )


class InitTestCase(unittest.TestCase):
    test_config_template_path = pathlib.Path(__file__).parent.joinpath(
        "config_template"
    )
    example_config_dict = DataPipelinesConfig(
        username="test_user",
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
                init_command,
                [str(self.test_config_template_path)],
                input="test_user\n/var/tmp",
            )
            self.assertEqual(0, result.exit_code)
            self.assertEqual(self.example_config_dict, read_config_or_exit())

    def test_global_config(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_commands.init.CONFIGURATION_PATH",
            pathlib.Path(tmp_dir).joinpath(".dp.yml"),
        ), patch(
            "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
            pathlib.Path(tmp_dir).joinpath(".dp.yml"),
        ):
            result = runner.invoke(init_command)
            self.assertEqual(0, result.exit_code)
            self.assertEqual(DEFAULT_GLOBAL_CONFIG, read_config_or_exit())
