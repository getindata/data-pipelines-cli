import json
import os
import pathlib
import shutil
import tempfile
import unittest
from typing import List
from unittest.mock import MagicMock, patch

import yaml
from click.testing import CliRunner

from data_pipelines_cli.cli import _cli
from data_pipelines_cli.cli_commands.deploy import DeployCommand
from data_pipelines_cli.errors import (
    AirflowDagsPathKeyError,
    DataPipelinesError,
    DependencyNotInstalledError,
)


def _noop():
    pass


class DeployCommandTestCase(unittest.TestCase):
    provider_args = {
        "schmoken": "/user/schmoken/path",
        "fooser": "user",
        "barsword": "password",
        "answer_to_universe_question": 42,
        "admin_favourite_colour": {
            "r": 255,
            "g": 0,
            "b": 255,
        },
        # `auto_mkdir` is not made up. When passed to LocalFileSystem, it
        # creates directories containing the file if necessary
        "auto_mkdir": True,
    }
    goldens_dir_path = pathlib.Path(__file__).parent.parent.joinpath("goldens")
    dbt_project_config = {"name": "test_project"}

    def setUp(self) -> None:
        blob_json_fd, self.blob_json_filename = tempfile.mkstemp(text=True)
        with open(blob_json_fd, "w") as f:
            yaml.dump(self.provider_args, f)

        self.dbt_project_config_dir = pathlib.Path(tempfile.mkdtemp())
        with open(self.dbt_project_config_dir.joinpath("dbt_project.yml"), "w") as f:
            yaml.dump(self.dbt_project_config, f)

        self.build_temp_dir = pathlib.Path(tempfile.mkdtemp())
        dags_path = pathlib.Path(self.build_temp_dir).joinpath("dag")
        dags_path.mkdir(parents=True)
        shutil.copytree(
            self.goldens_dir_path.joinpath("config"), dags_path.joinpath("config")
        )

        self.storage_uri = tempfile.mkdtemp()  # this way fsspec uses LocalFS

        self.subprocess_run_args = []

    def _mock_run(self, args: List[str]):
        self.subprocess_run_args = args

    def tearDown(self) -> None:
        shutil.rmtree(self.storage_uri)
        shutil.rmtree(self.build_temp_dir)
        shutil.rmtree(self.dbt_project_config_dir)
        os.remove(self.blob_json_filename)

    def test_blob_args_types(self):
        for dump, format_name in [(json.dump, "json"), (yaml.dump, "yaml")]:
            with self.subTest(format=format_name):
                runner = CliRunner()

                with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
                    dump(self.provider_args, tmp_file)

                result_provider_kwargs = {}

                def mock_init(
                    _self,
                    _env,
                    _docker_push,
                    _blob_address,
                    provider_kwargs_dict,
                    _datahub_ingest,
                ):
                    nonlocal result_provider_kwargs
                    result_provider_kwargs = provider_kwargs_dict

                with patch(
                    "data_pipelines_cli.cli_commands.deploy.DeployCommand.__init__",
                    mock_init,
                ), patch(
                    "data_pipelines_cli.cli_commands.deploy.DeployCommand.deploy",
                    lambda _self: _noop,
                ):
                    result = runner.invoke(
                        _cli, ["deploy", "--blob-args", tmp_file.name]
                    )
                self.assertEqual(0, result.exit_code, msg=result.exception)
                self.assertDictEqual(self.provider_args, result_provider_kwargs)

    @patch("data_pipelines_cli.cli_commands.deploy.BUILD_DIR", goldens_dir_path)
    def test_sync_bucket(self):
        # Worth noting: we are not extensively testing
        # 'filesystem_utils.LocalRemoteSync' here. It gets tested in
        # a dedicated 'test_filesystem_utils' file.
        runner = CliRunner()
        with patch("pathlib.Path.cwd", lambda: self.dbt_project_config_dir):
            result = runner.invoke(
                _cli,
                [
                    "deploy",
                    "--dags-path",
                    self.storage_uri,
                    "--blob-args",
                    self.blob_json_filename,
                ],
            )
        self.assertEqual(0, result.exit_code, msg=result.exception)
        self.assertEqual(
            2,
            len(os.listdir(self.storage_uri)),
        )

    def test_no_module_cli(self):
        for module_name, cli_args in [
            ("datahub", ["--datahub-ingest"]),
            ("docker", ["--docker-push"]),
        ]:
            with self.subTest(dep=module_name):
                runner = CliRunner()
                with patch.dict("sys.modules", **{module_name: None}), patch(
                    "pathlib.Path.cwd", lambda: self.dbt_project_config_dir
                ), patch(
                    "data_pipelines_cli.cli_constants.BUILD_DIR", self.build_temp_dir
                ):
                    result = runner.invoke(
                        _cli,
                        [
                            "deploy",
                            "--dags-path",
                            self.storage_uri,
                            "--blob-args",
                            self.blob_json_filename,
                            *cli_args,
                        ],
                    )
                self.assertEqual(1, result.exit_code)
                self.assertIsInstance(result.exception, DependencyNotInstalledError)

    def test_no_datahub_method(self):
        with patch.dict("sys.modules", datahub=None), patch(
            "pathlib.Path.cwd", lambda: self.dbt_project_config_dir
        ):
            with self.assertRaises(DependencyNotInstalledError):
                DeployCommand(
                    "base", False, self.storage_uri, self.provider_args, True
                ).deploy()

    @patch("data_pipelines_cli.cli_commands.deploy.BUILD_DIR", goldens_dir_path)
    def test_datahub_run(self):
        with patch("pathlib.Path.cwd", lambda: self.dbt_project_config_dir), patch(
            "data_pipelines_cli.cli_commands.deploy.subprocess_run", self._mock_run
        ), patch.dict("sys.modules", datahub=MagicMock()):
            DeployCommand(
                "base", False, self.storage_uri, self.provider_args, True
            ).deploy()
            self.assertListEqual(
                [
                    "datahub",
                    "ingest",
                    "-c",
                    f"{self.goldens_dir_path}/dag/config/base/datahub.yml",
                ],
                self.subprocess_run_args,
            )

    def test_no_docker_method(self):
        with patch.dict("sys.modules", docker=None), patch(
            "pathlib.Path.cwd", lambda: self.dbt_project_config_dir
        ), patch("data_pipelines_cli.cli_constants.BUILD_DIR", self.build_temp_dir):
            with self.assertRaises(DependencyNotInstalledError):
                DeployCommand(
                    "base", True, self.storage_uri, self.provider_args, False
                ).deploy()

    @patch(
        "data_pipelines_cli.cli_commands.deploy.BUILD_DIR",
        pathlib.Path("/tmp/some/non/ex/i/sting/path"),
    )
    def test_no_airflow_address(self):
        with self.assertRaises(AirflowDagsPathKeyError):
            DeployCommand("base", False, None, None, False)

    def test_airflow_address(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_commands.deploy.BUILD_DIR", pathlib.Path(tmp_dir)
        ):
            tmp_airflow_path = pathlib.Path(tmp_dir).joinpath(
                "dag", "config", "base", "airflow.yml"
            )
            tmp_airflow_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(
                self.goldens_dir_path.joinpath("config", "base", "airflow.yml"),
                tmp_airflow_path,
            )

            deploy_command = DeployCommand("base", False, None, None, False)
        self.assertEqual(
            "gcs://test-sync-project/sync-dir/dags/my-project-name",
            deploy_command.blob_address_path,
        )

    def test_staging_airflow_address(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.cli_commands.deploy.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch(
            "data_pipelines_cli.config_generation.BUILD_DIR",
            pathlib.Path(tmp_dir),
        ):
            for env in ["base", "staging"]:
                tmp_config_path = pathlib.Path(tmp_dir).joinpath("dag", "config", env)
                tmp_config_path.mkdir(parents=True, exist_ok=True)
                tmp_file_path = tmp_config_path.joinpath("airflow.yml")
                shutil.copyfile(
                    self.goldens_dir_path.joinpath("config", env, "airflow.yml"),
                    tmp_file_path,
                )

            deploy_command = DeployCommand("staging", False, None, None, False)
        self.assertEqual(
            "gcs://test/jinja/path/com/my/project/name",
            deploy_command.blob_address_path,
        )

    @patch("data_pipelines_cli.cli_commands.deploy.BUILD_DIR", goldens_dir_path)
    def test_docker_run(self):
        docker_kwargs = {}

        def _mock_docker(**kwargs):
            nonlocal docker_kwargs
            docker_kwargs = kwargs
            return []

        docker_images_mock = MagicMock()
        docker_images_mock.configure_mock(**{"push": _mock_docker})
        docker_client_mock = MagicMock()
        docker_client_mock.configure_mock(**{"images": docker_images_mock})
        docker_mock = MagicMock()
        docker_mock.configure_mock(**{"from_env": lambda: docker_client_mock})

        with patch.dict("sys.modules", docker=docker_mock), patch(
            "pathlib.Path.cwd", lambda: self.dbt_project_config_dir
        ), patch("docker.from_env", lambda: docker_client_mock), patch(
            "data_pipelines_cli.data_structures.git_revision_hash", lambda: "sha1234"
        ), patch(
            "data_pipelines_cli.cli_constants.BUILD_DIR", self.build_temp_dir
        ):
            DeployCommand(
                "base", True, self.storage_uri, self.provider_args, False
            ).deploy()

        self.assertEqual("my_docker_repository_uri", docker_kwargs.get("repository"))
        self.assertEqual("sha1234", docker_kwargs.get("tag"))

    @patch("data_pipelines_cli.cli_commands.deploy.BUILD_DIR", goldens_dir_path)
    def test_docker_error(self):
        def _mock_docker(**_kwargs):
            return [
                '{"status":"The push refers to repository [docker.io/library/rep]"}',
                '{"errorDetail":{"message":"An image does not exist locally with '
                'the tag: rep"},"error":"An image does not exist locally with '
                'the tag: rep"}',
            ]

        docker_images_mock = MagicMock()
        docker_images_mock.configure_mock(**{"push": _mock_docker})
        docker_client_mock = MagicMock()
        docker_client_mock.configure_mock(**{"images": docker_images_mock})
        docker_mock = MagicMock()
        docker_mock.configure_mock(**{"from_env": lambda: docker_client_mock})

        with patch("pathlib.Path.cwd", lambda: self.dbt_project_config_dir), patch.dict(
            "sys.modules", docker=docker_mock
        ), patch(
            "data_pipelines_cli.data_structures.git_revision_hash", lambda: "sha1234"
        ), patch(
            "data_pipelines_cli.cli_constants.BUILD_DIR", self.build_temp_dir
        ):
            with self.assertRaises(DataPipelinesError):
                DeployCommand(
                    "base", True, self.storage_uri, self.provider_args, False
                ).deploy()
