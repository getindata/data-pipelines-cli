import pathlib
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from data_pipelines_cli.cli_commands.template import list_templates_command
from data_pipelines_cli.data_structures import (
    DataPipelinesConfig,
    TemplateConfig,
    read_config_or_exit,
)
from data_pipelines_cli.filesystem_utils import FilesystemProvider


class MyTestCase(unittest.TestCase):
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
        blob_protocol=FilesystemProvider.GCP.value,
    )
    example_config_path = pathlib.Path(__file__).parent.joinpath("example_config.yml")

    def test_read_config(self):
        with patch(
            "data_pipelines_cli.data_structures.CONFIGURATION_PATH",
            self.example_config_path,
        ):
            self.assertEqual(self.example_config_dict, read_config_or_exit())

    def test_list_templates(self):
        runner = CliRunner()
        with patch(
            "data_pipelines_cli.data_structures.CONFIGURATION_PATH",
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
