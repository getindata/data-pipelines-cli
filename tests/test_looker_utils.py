import os
import pathlib
import shutil
import tempfile
import unittest
from os import PathLike
from typing import Any
from unittest.mock import MagicMock, patch

from data_pipelines_cli.looker_utils import deploy_lookML_model, generate_lookML_model

goldens_dir_path = pathlib.Path(__file__).parent.joinpath("goldens")


class LookerUtilsTestCase(unittest.TestCase):

    dbt_project = {
        "config-version": 2,
        "name": "my_test_project_1338_sources",
        "version": "1.2.3",
        "source-paths": ["models"],
    }

    def setUp(self) -> None:
        self.build_temp_dir = pathlib.Path(tempfile.mkdtemp())
        dags_path = pathlib.Path(self.build_temp_dir).joinpath("dag")
        dags_path.mkdir(parents=True)
        shutil.copytree(goldens_dir_path.joinpath("config"), dags_path.joinpath("config"))
        shutil.copytree(goldens_dir_path.joinpath("lookml"), self.build_temp_dir.joinpath("lookml"))

    def tearDown(self) -> None:
        shutil.rmtree(self.build_temp_dir)

    def mock_origin(self, name: str):
        self.origin = MagicMock()
        self.origin.push = MagicMock()
        return self.origin

    def mock_clone_from(self, url: PathLike, to_path: PathLike, **kwargs: Any):
        self.assertEqual("https://gitlab.com/getindata/dataops/some_looker_repo.git", url)
        self.assertEqual("master", kwargs["branch"])

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
    def test_bi_deploy_looker(self):
        with patch("data_pipelines_cli.looker_utils.BUILD_DIR", self.build_temp_dir), patch(
            "data_pipelines_cli.looker_utils.Repo", self.repo_class_mock()
        ), patch("data_pipelines_cli.looker_utils._deploy_looker_project_to_production"), patch(
            "data_pipelines_cli.looker_utils.LOOKML_DEST_PATH",
            self.build_temp_dir.joinpath("lookml"),
        ):
            deploy_lookML_model("/path/to/key", "env")

        self.assertTrue(
            os.path.exists(
                self.build_temp_dir.joinpath(
                    "looker_project_repo", "dp_code", "views", "view1.view.lkml"
                )
            )
        )
        self.assertTrue(
            os.path.exists(
                self.build_temp_dir.joinpath(
                    "looker_project_repo", "dp_code", "models", "model1.model.lkml"
                )
            )
        )
        self.assertTrue(
            os.path.exists(
                self.build_temp_dir.joinpath("looker_project_repo", "dp_code", "readme.txt")
            )
        )

    def test_bi_compile_looker(self):
        subprocess_run_mock = MagicMock()
        with patch("data_pipelines_cli.looker_utils.subprocess_run", subprocess_run_mock), patch(
            "data_pipelines_cli.looker_utils.LOOKML_DEST_PATH", "/path/for/lookml"
        ):
            generate_lookML_model()

        subprocess_run_mock.assert_called_once_with(
            ["dbt2looker", "--output-dir", "/path/for/lookml"]
        )
