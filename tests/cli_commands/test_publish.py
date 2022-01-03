import pathlib
import shutil
import tempfile
import unittest
from unittest.mock import patch

import yaml
from click.testing import CliRunner

from data_pipelines_cli.cli import _cli

goldens_dir_path = pathlib.Path(__file__).parent.parent.joinpath("goldens")


class PublishCommandTestCase(unittest.TestCase):
    expected_sources = {
        "version": 2,
        "sources": [
            {
                "name": "my_test_project_1337",
                "database": "example-project",
                "tags": ["project:my_test_project_1337"],
                "meta": {"dag": "experimental-dag"},
                "tables": [
                    {
                        "name": "my_first_dbt_model",
                        "description": "A starter dbt model",
                        "columns": [
                            {
                                "name": "id",
                                "description": "The primary key for this table",
                            }
                        ],
                    },
                    {
                        "name": "my_second_dbt_model",
                        "description": "A starter dbt model",
                        "columns": [
                            {
                                "name": "id",
                                "description": "The primary key for this table",
                            }
                        ],
                    },
                ],
            }
        ],
    }
    dbt_project = {
        "config-version": 2,
        "name": "my_test_project_1337_sources",
        "version": "1.2.3",
        "source-paths": ["models"],
    }

    def setUp(self) -> None:
        self.maxDiff = None

        self.build_temp_dir = pathlib.Path(tempfile.mkdtemp())
        dags_path = pathlib.Path(self.build_temp_dir).joinpath("dag")
        dags_path.mkdir(parents=True)
        shutil.copytree(
            goldens_dir_path.joinpath("config"), dags_path.joinpath("config")
        )

        profiles_yml_path = pathlib.Path(self.build_temp_dir).joinpath(
            "profiles", "env_execution", "profiles.yml"
        )
        profiles_yml_path.parent.mkdir(parents=True)
        shutil.copyfile(
            goldens_dir_path.joinpath("example_profiles", "dev_bigquery.yml"),
            profiles_yml_path,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.build_temp_dir)

    @patch("pathlib.Path.cwd", lambda: goldens_dir_path)
    def test_generate_correct_project(self):
        runner = CliRunner()

        with patch(
            "data_pipelines_cli.cli_commands.publish.BUILD_DIR", self.build_temp_dir
        ), patch("data_pipelines_cli.config_generation.BUILD_DIR", self.build_temp_dir):
            result = runner.invoke(_cli, ["publish"])
            self.assertEqual(0, result.exit_code, msg=result.exception)

            with open(
                pathlib.Path(self.build_temp_dir).joinpath(
                    "package", "models", "sources.yml"
                ),
                "r",
            ) as sources_yml:
                self.assertDictEqual(self.expected_sources, yaml.safe_load(sources_yml))
            with open(
                pathlib.Path(self.build_temp_dir).joinpath(
                    "package", "dbt_project.yml"
                ),
                "r",
            ) as dbt_project_yml:
                self.assertDictEqual(self.dbt_project, yaml.safe_load(dbt_project_yml))
