import pathlib
import unittest
from unittest.mock import patch

from click.testing import CliRunner

import data_pipelines_cli.cli as cli
from data_pipelines_cli.cli import DataPipelinesConfig, TemplateConfig


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
    )
    example_config_path = pathlib.Path(__file__).parent.joinpath(
        "example_config.yml"
    )

    def test_read_config(self):
        with patch(
            "data_pipelines_cli.cli.CONFIGURATION_PATH",
            self.example_config_path,
        ):
            self.assertEqual(
                self.example_config_dict, cli.read_config_or_exit()
            )

    def test_list_templates(self):
        runner = CliRunner()
        with patch(
            "data_pipelines_cli.cli.CONFIGURATION_PATH",
            self.example_config_path,
        ):
            result = runner.invoke(cli.list_templates)
            self.assertEqual(0, result.exit_code)
            self.assertEqual(
                "AVAILABLE TEMPLATES:\n\n"
                "template_name: template1\n"
                "template_path: https://example.com/xyz/abcd.git\n\n"
                "template_name: template2\n"
                "template_path: https://example.com/git/example.git\n\n",
                result.output,
            )
