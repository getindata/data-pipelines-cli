import json
import os
import pathlib
import tempfile
import unittest
from typing import List
from unittest.mock import MagicMock, patch

import yaml
from click.testing import CliRunner

from data_pipelines_cli.cli import _cli
from data_pipelines_cli.errors import DockerNotInstalledError

goldens_dir_path = pathlib.Path(__file__).parent.parent.joinpath("goldens")


class CompileCommandTestCase(unittest.TestCase):
    @staticmethod
    def _datahub_content(ingest_endpoint):
        return {"sink": {"config": {"server": f"https://{ingest_endpoint}:8080"}}}

    @staticmethod
    def _k8s_content(repository_url: str, tag: str):
        return {
            "image": {
                "repository": repository_url,
                "tag": tag,
            },
            "variable1": 1337,
            "var2": "Hello, world!",
            "envs": {
                "SOME_BOOLEAN": True,
            },
        }

    def setUp(self) -> None:
        self.all_subprocess_run_args = []

    def _mock_run(self, args: List[str]):
        self.all_subprocess_run_args += args

    @patch("pathlib.Path.cwd", lambda: goldens_dir_path)
    @patch("data_pipelines_cli.data_structures.git_revision_hash")
    def test_no_args(self, mock_git_revision_hash):
        commit_sha = "aaa9876aaa"
        mock_git_revision_hash.return_value = commit_sha

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_commands.compile.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.config_generation.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.cli_constants.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.dbt_utils.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.dbt_utils.subprocess_run", self._mock_run
        ):
            result = runner.invoke(_cli, ["compile"])
            self.assertEqual(0, result.exit_code, msg=result.exception)

            # 4 = 2 from goldens/dag, manifest.json, 'config' directory
            self.assertEqual(4, len(os.listdir(pathlib.Path(tmp_dir).joinpath("dag"))))

            args_str = " ".join(self.all_subprocess_run_args)
            self.assertIn("dbt deps", args_str)
            self.assertIn("dbt compile", args_str)
            self.assertIn("dbt docs generate", args_str)
            self.assertIn("dbt source freshness", args_str)

            tmp_dir_path = pathlib.Path(tmp_dir)
            with open(
                tmp_dir_path.joinpath("dag", "manifest.json"), "r"
            ) as tmp_manifest, open(
                goldens_dir_path.joinpath("target", "manifest.json"), "r"
            ) as golden_manifest:
                self.assertDictEqual(
                    json.load(golden_manifest), json.load(tmp_manifest)
                )
            with open(
                tmp_dir_path.joinpath("dag", "config", "base", "datahub.yml"), "r"
            ) as tmp_datahub, open(
                goldens_dir_path.joinpath("config", "base", "datahub.yml")
            ) as golden_datahub:
                self.assertDictEqual(
                    yaml.safe_load(golden_datahub), yaml.safe_load(tmp_datahub)
                )
            with open(
                tmp_dir_path.joinpath("dag", "config", "base", "k8s.yml"), "r"
            ) as tmp_k8s:
                self.assertDictEqual(
                    self._k8s_content("my_docker_repository_uri", "aaa9876aaa"),
                    yaml.safe_load(tmp_k8s),
                )

    @patch("pathlib.Path.cwd", lambda: goldens_dir_path)
    @patch("data_pipelines_cli.data_structures.git_revision_hash")
    def test_docker_not_installed(self, mock_git_revision_hash):
        commit_sha = "aaa9876aaa"
        mock_git_revision_hash.return_value = commit_sha

        runner = CliRunner()
        with patch.dict(
            "sys.modules", docker=None
        ), tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_commands.compile.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.config_generation.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.cli_constants.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.dbt_utils.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.dbt_utils.subprocess_run", self._mock_run
        ):
            result = runner.invoke(
                _cli,
                ["compile", "--docker-build"],
            )
        self.assertEqual(1, result.exit_code)
        self.assertIsInstance(result.exception, DockerNotInstalledError)

    @patch("pathlib.Path.cwd", lambda: goldens_dir_path)
    @patch("data_pipelines_cli.data_structures.git_revision_hash")
    def test_docker_uri_build(self, mock_git_revision_hash):
        commit_sha = "aaa9876aaa"
        mock_git_revision_hash.return_value = commit_sha

        docker_tag = None

        def _mock_docker(**kwargs):
            nonlocal docker_tag
            docker_tag = kwargs["tag"]
            return None, []

        docker_images_mock = MagicMock()
        docker_images_mock.configure_mock(**{"build": _mock_docker})
        docker_client_mock = MagicMock()
        docker_client_mock.configure_mock(**{"images": docker_images_mock})
        docker_mock = MagicMock()
        docker_mock.configure_mock(**{"from_env": lambda: docker_client_mock})

        runner = CliRunner()
        with patch.dict(
            "sys.modules", docker=docker_mock
        ), tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_commands.compile.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.cli_constants.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.config_generation.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.dbt_utils.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.dbt_utils.subprocess_run", self._mock_run
        ):
            result = runner.invoke(_cli, ["compile", "--docker-build"])
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertEqual("my_docker_repository_uri:aaa9876aaa", docker_tag)
