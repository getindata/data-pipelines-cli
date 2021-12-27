import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from data_pipelines_cli.data_structures import (
    DataPipelinesConfig,
    DockerArgs,
    TemplateConfig,
    read_config,
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
    example_config_path = pathlib.Path(__file__).parent.joinpath(
        "goldens", "example_config.yml"
    )

    def test_read_config(self):
        with patch(
            "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
            self.example_config_path,
        ):
            self.assertEqual(self.example_config_dict, read_config())

    def test_read_config_no_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_constants.CONFIGURATION_PATH",
            pathlib.Path(tmp_dir).joinpath("non_existing_file.yml"),
        ):
            with self.assertRaises(NoConfigFileError):
                read_config()


class DockerArgsTest(unittest.TestCase):
    @patch("data_pipelines_cli.data_structures.git_revision_hash")
    def test_build_tag(self, mock_git_revision_hash):
        repository = "rep"
        commit_sha = "eee440bfbe0801ec3f533f897c1d55e6a5afd5cd"
        mock_git_revision_hash.return_value = commit_sha

        docker_args = DockerArgs(repository)
        self.assertEqual(f"{repository}:{commit_sha}", docker_args.docker_build_tag())
        self.assertEqual(repository, docker_args.repository)
        self.assertEqual(commit_sha, docker_args.commit_sha)

    @patch("data_pipelines_cli.data_structures.git_revision_hash")
    def test_no_git_hash(self, mock_git_revision_hash):
        mock_git_revision_hash.return_value = None

        with self.assertRaises(DataPipelinesError):
            _ = DockerArgs("rep")

    @patch("data_pipelines_cli.data_structures.git_revision_hash")
    @patch.dict(os.environ, {"REPOSITORY_URL": "repo"})
    def test_no_repository_argument(self, mock_git_revision_hash):
        commit_sha = "eee440bfbe0801ec3f533f897c1d55e6a5afd5cd"
        mock_git_revision_hash.return_value = commit_sha

        docker_args = DockerArgs(None)
        self.assertEqual("repo", docker_args.repository)
        self.assertEqual(commit_sha, docker_args.commit_sha)
