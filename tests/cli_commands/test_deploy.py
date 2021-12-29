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
from data_pipelines_cli.errors import DataPipelinesError, DependencyNotInstalledError


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

        self.storage_uri = tempfile.mkdtemp()  # this way fsspec uses LocalFS

        self.subprocess_run_args = []

    def _mock_run(self, args: List[str]):
        self.subprocess_run_args = args

    def tearDown(self) -> None:
        shutil.rmtree(self.storage_uri)
        shutil.rmtree(self.dbt_project_config_dir)
        os.remove(self.blob_json_filename)

    def test_deploy_no_args(self):
        runner = CliRunner()
        result = runner.invoke(_cli, ["deploy"])
        self.assertEqual(0, result.exit_code, msg=result.exception)
        self.assertRegex(result.output, r"^Usage: .* deploy .*")

    def test_blob_args_types(self):
        for dump, format_name in [(json.dump, "json"), (yaml.dump, "yaml")]:
            with self.subTest(format=format_name):
                runner = CliRunner()

                with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
                    dump(self.provider_args, tmp_file)

                result_provider_kwargs = {}
                result_blob_address = ""

                def mock_init(
                    _self,
                    _docker_push,
                    blob_address,
                    provider_kwargs_dict,
                    _datahub_ingest,
                ):
                    nonlocal result_provider_kwargs
                    nonlocal result_blob_address
                    result_provider_kwargs = provider_kwargs_dict
                    result_blob_address = blob_address

                with patch(
                    "data_pipelines_cli.cli_commands.deploy.DeployCommand.__init__",
                    mock_init,
                ), patch(
                    "data_pipelines_cli.cli_commands.deploy.DeployCommand.deploy",
                    lambda _self: _noop,
                ):
                    result = runner.invoke(
                        _cli, ["deploy", self.storage_uri, "--blob-args", tmp_file.name]
                    )
                self.assertEqual(0, result.exit_code, msg=result.exception)
                self.assertDictEqual(self.provider_args, result_provider_kwargs)
                self.assertEqual(self.storage_uri, result_blob_address)

    @patch("data_pipelines_cli.cli_commands.deploy.BUILD_DIR", goldens_dir_path)
    def test_sync_bucket(self):
        # Worth noting: we are not extensively testing
        # 'filesystem_utils.LocalRemoteSync' here. It gets tested in
        # a dedicated 'test_filesystem_utils' file.
        runner = CliRunner()
        with patch("pathlib.Path.cwd", lambda _: self.dbt_project_config_dir):
            result = runner.invoke(
                _cli,
                ["deploy", self.storage_uri, "--blob-args", self.blob_json_filename],
            )
        self.assertEqual(0, result.exit_code, msg=result.exception)
        self.assertEqual(
            2,
            len(
                os.listdir(
                    pathlib.Path(self.storage_uri).joinpath(
                        "dags", self.dbt_project_config["name"]
                    )
                )
            ),
        )

    def test_no_module_cli(self):
        for module_name, cli_args in [
            ("datahub", ["--datahub-ingest"]),
            ("docker", ["--docker-push", "rep"]),
        ]:
            with self.subTest(dep=module_name):
                runner = CliRunner()
                with patch.dict("sys.modules", **{module_name: None}), patch(
                    "pathlib.Path.cwd", lambda _: self.dbt_project_config_dir
                ):
                    result = runner.invoke(
                        _cli,
                        [
                            "deploy",
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
            "pathlib.Path.cwd", lambda _: self.dbt_project_config_dir
        ):
            with self.assertRaises(DependencyNotInstalledError):
                DeployCommand(None, self.storage_uri, self.provider_args, True).deploy()

    @patch("data_pipelines_cli.cli_commands.deploy.BUILD_DIR", goldens_dir_path)
    def test_datahub_run(self):
        with patch("pathlib.Path.cwd", lambda _: self.dbt_project_config_dir), patch(
            "data_pipelines_cli.cli_commands.deploy.subprocess_run", self._mock_run
        ), patch.dict("sys.modules", datahub=MagicMock()):
            DeployCommand(None, self.storage_uri, self.provider_args, True).deploy()
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
            "pathlib.Path.cwd", lambda _: self.dbt_project_config_dir
        ):
            with self.assertRaises(DependencyNotInstalledError):
                DeployCommand(
                    "rep", self.storage_uri, self.provider_args, False
                ).deploy()

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
            "pathlib.Path.cwd", lambda _: self.dbt_project_config_dir
        ), patch("docker.from_env", lambda: docker_client_mock), patch(
            "data_pipelines_cli.data_structures.git_revision_hash", lambda: "sha1234"
        ):
            DeployCommand("rep", self.storage_uri, self.provider_args, False).deploy()

        self.assertEqual("rep", docker_kwargs.get("repository"))
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

        with patch(
            "pathlib.Path.cwd", lambda _: self.dbt_project_config_dir
        ), patch.dict("sys.modules", docker=docker_mock), patch(
            "data_pipelines_cli.data_structures.git_revision_hash", lambda: "sha1234"
        ):

            with self.assertRaises(DataPipelinesError):
                DeployCommand(
                    "rep", self.storage_uri, self.provider_args, False
                ).deploy()
