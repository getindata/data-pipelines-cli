import json
import pathlib
import shutil
import tempfile
import unittest
from os import PathLike
from typing import Any
from unittest.mock import MagicMock, patch

import yaml
from click.testing import CliRunner

from data_pipelines_cli.cli import _cli
from data_pipelines_cli.cli_commands.publish import create_package
from data_pipelines_cli.errors import DataPipelinesError

goldens_dir_path = pathlib.Path(__file__).parent.parent.joinpath("goldens")


class PublishCommandTestCase(unittest.TestCase):
    expected_sources = {
        "version": 2,
        "sources": [
            {
                "name": "my_test_project_1337",
                "database": "example-project",
                "schema": "username_private_working_dataset",
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
                                "meta": {},
                                "quote": None,
                                "tags": [],
                            }
                        ],
                        "meta": {},
                        "tags": [],
                    },
                    {
                        "name": "my_second_dbt_model",
                        "description": "A starter dbt model",
                        "columns": [
                            {
                                "name": "id",
                                "description": "The primary key for this table",
                                "meta": {},
                                "quote": None,
                                "tags": [],
                            }
                        ],
                        "meta": {},
                        "tags": [],
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
        shutil.copytree(goldens_dir_path.joinpath("config"), dags_path.joinpath("config"))

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

    def mock_origin(self, name: str):
        self.origin = MagicMock()
        self.origin.push = MagicMock()
        return self.origin

    def mock_clone_from(self, url: PathLike, to_path: PathLike, **kwargs: Any):
        self.assertEqual("https://gitlab.com/getindata/dataops/some_repo.git", url)
        self.assertEqual("main", kwargs["branch"])

        def noop():
            pass

        repo_mock = MagicMock()
        self.git = MagicMock()
        self.index = MagicMock()
        self.index.commit = MagicMock()
        self.git.add = MagicMock()
        config_writer_mock = MagicMock()
        set_value_mock = MagicMock()
        set_value_mock.configure_mock(**{"release": noop})
        config_writer_mock.configure_mock(**{"set_value": lambda x, y, z: set_value_mock})
        repo_mock.configure_mock(
            **{
                "config_writer": config_writer_mock,
                "git": self.git,
                "index": self.index,
                "remote": self.mock_origin,
            }
        )
        return repo_mock

    def repo_class_mock(self):
        self.repo_mock_class = MagicMock()
        self.repo_mock_class.configure_mock(**{"clone_from": self.mock_clone_from})
        return self.repo_mock_class

    @patch("pathlib.Path.cwd", lambda: goldens_dir_path)
    def test_generate_correct_project(self):
        runner = CliRunner()
        with patch("data_pipelines_cli.cli_commands.publish.BUILD_DIR", self.build_temp_dir), patch(
            "data_pipelines_cli.config_generation.BUILD_DIR", self.build_temp_dir
        ), patch("data_pipelines_cli.cli_commands.publish.Repo", self.repo_class_mock()):
            runner.invoke(_cli, ["publish", "--key-path", "SOME_KEY.txt"])
            result = runner.invoke(_cli, ["publish", "--key-path", "SOME_KEY.txt"])

            self.verify_status_code(result)
            self.verify_publications()
            self.verify_generated_files()

    def verify_status_code(self, result):
        self.assertEqual(0, result.exit_code, msg=result.output)

    def verify_publications(self):
        self.git.add.assert_called_with(all=True)
        self.index.commit.assert_called_with(
            "Publication from project my_test_project_1337, version: 1.2.3"
        )
        self.origin.push.assert_called_with()

    def verify_generated_files(self):
        with open(
            pathlib.Path(self.build_temp_dir).joinpath("package", "models", "sources.yml"),
            "r",
        ) as sources_yml:
            self.assertDictEqual(self.expected_sources, yaml.safe_load(sources_yml))
        with open(
            pathlib.Path(self.build_temp_dir).joinpath("package", "dbt_project.yml"),
            "r",
        ) as dbt_project_yml:
            self.assertDictEqual(self.dbt_project, yaml.safe_load(dbt_project_yml))

    def test_no_models(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "pathlib.Path.cwd", lambda: pathlib.Path(tmp_dir)
        ):
            shutil.copyfile(
                goldens_dir_path.joinpath("dbt_project.yml"),
                pathlib.Path(tmp_dir).joinpath("dbt_project.yml"),
            )

            target_path = pathlib.Path(tmp_dir).joinpath("target")
            target_path.mkdir(parents=True)
            with open(
                goldens_dir_path.joinpath("target", "manifest.json"), "r"
            ) as manifest_json, open(target_path.joinpath("manifest.json"), "w") as tmp_manifest:
                manifest = json.load(manifest_json)
                for k in list(manifest["nodes"].keys()):
                    if k.startswith("model"):
                        del manifest["nodes"][k]
                json.dump(manifest, tmp_manifest)
            with self.assertRaises(DataPipelinesError):
                create_package()
