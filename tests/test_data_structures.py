import pathlib
import shutil
import tempfile
import unittest
from unittest.mock import patch

from data_pipelines_cli.data_structures import (
    DataPipelinesConfig,
    DockerArgs,
    TemplateConfig,
    read_env_config,
)
from data_pipelines_cli.errors import DataPipelinesError, NoConfigFileError


class DataStructuresTestCase(unittest.TestCase):
    example_config_dict = DataPipelinesConfig(
        templates={
            "template1": TemplateConfig(
                template_name="template1",
                template_path="https://example.com/xyz/abcd.git",
            ),
            "template2": TemplateConfig(
                template_name="template2",
                template_path="https://example.com/git/example.git",
            ),
            "create_test": TemplateConfig(
                template_name="create_test",
                template_path="source_path",
            ),
        },
        vars={"username": "testuser"},
    )
    example_config_path = pathlib.Path(__file__).parent.joinpath("goldens", "example_config.yml")

    def test_read_config(self):
        with patch(
            "data_pipelines_cli.cli_constants.ENV_CONFIGURATION_PATH",
            self.example_config_path,
        ):
            self.assertEqual(self.example_config_dict, read_env_config())

    def test_read_config_no_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_constants.ENV_CONFIGURATION_PATH",
            pathlib.Path(tmp_dir).joinpath("non_existing_file.yml"),
        ):
            with self.assertRaises(NoConfigFileError):
                read_env_config()


class DockerArgsTest(unittest.TestCase):
    goldens_dir_path = pathlib.Path(__file__).parent.joinpath("goldens")

    def setUp(self) -> None:
        self.build_temp_dir = pathlib.Path(tempfile.mkdtemp())
        dags_path = pathlib.Path(self.build_temp_dir).joinpath("dag")
        dags_path.mkdir(parents=True)
        shutil.copytree(self.goldens_dir_path.joinpath("config"), dags_path.joinpath("config"))

    def tearDown(self) -> None:
        shutil.rmtree(self.build_temp_dir)

    @patch("data_pipelines_cli.data_structures.git_revision_hash")
    def test_build_tag(self, mock_git_revision_hash):
        repository = "my_docker_repository_uri"
        commit_sha = "eee440bfbe0801ec3f533f897c1d55e6a5afd5cd"
        mock_git_revision_hash.return_value = commit_sha

        with patch("data_pipelines_cli.cli_constants.BUILD_DIR", self.build_temp_dir):
            docker_args = DockerArgs("base")

        self.assertEqual(f"{repository}:{commit_sha}", docker_args.docker_build_tag())
        self.assertEqual(repository, docker_args.repository)
        self.assertEqual(commit_sha, docker_args.commit_sha)

    @patch("data_pipelines_cli.cli_constants.BUILD_DIR", goldens_dir_path)
    @patch("data_pipelines_cli.data_structures.git_revision_hash")
    def test_no_repository(self, mock_git_revision_hash):
        commit_sha = "eee440bfbe0801ec3f533f897c1d55e6a5afd5cd"
        mock_git_revision_hash.return_value = commit_sha

        with self.assertRaises(DataPipelinesError):
            _ = DockerArgs("base")

    @patch("data_pipelines_cli.data_structures.git_revision_hash")
    def test_no_git_hash(self, mock_git_revision_hash):
        mock_git_revision_hash.return_value = None

        with patch("data_pipelines_cli.cli_constants.BUILD_DIR", self.build_temp_dir):
            with self.assertRaises(DataPipelinesError):
                _ = DockerArgs("base")
