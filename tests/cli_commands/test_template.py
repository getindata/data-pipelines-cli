import pathlib
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from data_pipelines_cli.cli import _cli


class TemplateCommandTestCase(unittest.TestCase):
    example_config_path = pathlib.Path(__file__).parent.parent.joinpath(
        "goldens", "example_config.yml"
    )

    def test_list_templates(self):
        runner = CliRunner()
        with patch(
            "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
            self.example_config_path,
        ):
            result = runner.invoke(_cli, ["template-list"])
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual(
                "AVAILABLE TEMPLATES:\n\n"
                "template_name: template1\n"
                "template_path: https://example.com/xyz/abcd.git\n\n"
                "template_name: template2\n"
                "template_path: https://example.com/git/example.git\n\n"
                "template_name: create_test\n"
                "template_path: source_path\n\n",
                result.output,
            )
