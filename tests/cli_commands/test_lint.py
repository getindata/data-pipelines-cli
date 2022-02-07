import pathlib
import shutil
import tempfile
import unittest
from typing import List
from unittest.mock import MagicMock, patch

import yaml
from click.testing import CliRunner

from data_pipelines_cli.cli import _cli
from data_pipelines_cli.cli_commands.lint import (
    _get_dialect_or_default,
    _get_source_tests_paths,
)
from data_pipelines_cli.errors import SQLLintError, SubprocessNonZeroExitError

goldens_dir_path = pathlib.Path(__file__).parent.parent.joinpath("goldens")


@patch("data_pipelines_cli.cli_commands.lint.generate_profiles_yml", MagicMock())
class LintCommandTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.linted_sqls = []
        self.subprocess_run_args = []

        self.dbt_project_tmp_dir = pathlib.Path(tempfile.mkdtemp())
        shutil.copyfile(
            goldens_dir_path.joinpath("dbt_project.yml"),
            self.dbt_project_tmp_dir.joinpath("dbt_project.yml"),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.dbt_project_tmp_dir)

    def _mock_run(self, args: List[str]):
        self.subprocess_run_args.append(args)

    def _mock_run_raise_error(self, args: List[str]):
        self.subprocess_run_args.append(args)
        raise SubprocessNonZeroExitError("sqlfluff", 65)

    @patch("data_pipelines_cli.cli_commands.lint.BUILD_DIR", pathlib.Path("/a/b/c/d/e/f"))
    def test_lint_sqls_with_errors(self):
        with patch("pathlib.Path.cwd", lambda: pathlib.Path(self.dbt_project_tmp_dir)), patch(
            "data_pipelines_cli.cli_commands.lint.subprocess_run", self._mock_run_raise_error
        ):
            runner = CliRunner()
            result = runner.invoke(_cli, ["lint", "--no-fix"])
            self.assertEqual(
                1, result.exit_code, msg="\n".join([str(result.exception), str(result.output)])
            )
            self.assertIsInstance(result.exception, SQLLintError)
            self.assertTrue(any(["lint" in sargs for sargs in self.subprocess_run_args]))
            self.assertFalse(any(["fix" in sargs for sargs in self.subprocess_run_args]))

    @patch("data_pipelines_cli.cli_commands.lint.BUILD_DIR", pathlib.Path("/a/b/c/d/e/f"))
    def test_lint_sqls_without_errors(self):
        with patch("pathlib.Path.cwd", lambda: pathlib.Path(self.dbt_project_tmp_dir)), patch(
            "data_pipelines_cli.cli_commands.lint.subprocess_run", self._mock_run
        ):
            runner = CliRunner()
            result = runner.invoke(_cli, ["lint", "--no-fix"])
            self.assertEqual(
                0, result.exit_code, msg="\n".join([str(result.exception), str(result.output)])
            )
            self.assertTrue(any(["lint" in sargs for sargs in self.subprocess_run_args]))
            self.assertFalse(any(["fix" in sargs for sargs in self.subprocess_run_args]))

    @patch("data_pipelines_cli.cli_commands.lint.BUILD_DIR", pathlib.Path("/a/b/c/d/e/f"))
    def test_fix_sqls(self):
        with patch("pathlib.Path.cwd", lambda: pathlib.Path(self.dbt_project_tmp_dir)), patch(
            "data_pipelines_cli.cli_commands.lint.subprocess_run", self._mock_run
        ):
            runner = CliRunner()
            result = runner.invoke(_cli, ["lint"])
            self.assertEqual(
                0, result.exit_code, msg="\n".join([str(result.exception), str(result.output)])
            )
            self.assertTrue(any(["lint" in sargs for sargs in self.subprocess_run_args]))
            self.assertTrue(any(["fix" in sargs for sargs in self.subprocess_run_args]))

    @patch("data_pipelines_cli.cli_commands.lint.BUILD_DIR", pathlib.Path("/a/b/c/d/e/f"))
    @patch("data_pipelines_cli.cli_commands.lint.subprocess_run")
    def test_raise_unexpected_error(self, subprocess_mock):
        for err in [
            ConnectionAbortedError,
            FileNotFoundError,
            FileExistsError,
            KeyError,
            FloatingPointError,
        ]:
            with self.subTest(exception=err), patch(
                "pathlib.Path.cwd", lambda: pathlib.Path(self.dbt_project_tmp_dir)
            ):
                subprocess_mock.side_effect = err
                runner = CliRunner()
                result = runner.invoke(_cli, ["lint", "--no-fix"])
                self.assertEqual(
                    1, result.exit_code, msg="\n".join([str(result.exception), str(result.output)])
                )
                self.assertIsInstance(result.exception, err)

    @patch("data_pipelines_cli.cli_commands.lint.BUILD_DIR", pathlib.Path("/a/b/c/d/e/f"))
    @patch("data_pipelines_cli.cli_commands.lint.subprocess_run")
    def test_raise_different_subprocess_error(self, subprocess_mock):
        subprocess_mock.side_effect = SubprocessNonZeroExitError("sqlfluff", 248)

        with patch("pathlib.Path.cwd", lambda: pathlib.Path(self.dbt_project_tmp_dir)):
            runner = CliRunner()
            result = runner.invoke(_cli, ["lint", "--no-fix"])
        self.assertEqual(
            1, result.exit_code, msg="\n".join([str(result.exception), str(result.output)])
        )
        self.assertIsInstance(result.exception, SubprocessNonZeroExitError)
        self.assertEqual(248, result.exception.exit_code)

    @patch("data_pipelines_cli.cli_commands.lint.BUILD_DIR", pathlib.Path("/a/b/c/d/e/f"))
    @patch("data_pipelines_cli.cli_commands.lint.subprocess_run")
    def test_raise_wrong_dialect_error(self, subprocess_mock):
        subprocess_mock.side_effect = SubprocessNonZeroExitError("sqlfluff", 66)

        with patch("pathlib.Path.cwd", lambda: pathlib.Path(self.dbt_project_tmp_dir)), patch(
            "data_pipelines_cli.cli_commands.lint._get_dialect_or_default", lambda: "some_dialect"
        ):
            runner = CliRunner()
            runner.invoke(_cli, ["lint"])
        self.assertEqual(2, subprocess_mock.call_count)


class LintHelperFunctionsTestCase(unittest.TestCase):
    def test_get_dialect(self):
        build_dir_mock = MagicMock()
        build_dir_mock.configure_mock(**{"joinpath": lambda _self, *_args: goldens_dir_path})

        with patch("data_pipelines_cli.cli_commands.lint.BUILD_DIR", build_dir_mock):
            self.assertEqual("bigquery", _get_dialect_or_default())

    @patch("data_pipelines_cli.cli_commands.lint.BUILD_DIR", pathlib.Path("/a/b/c/d/e/f"))
    @patch("pathlib.Path.cwd", lambda: goldens_dir_path)
    def test_get_dialect_no_build_dir(self):
        self.assertEqual("bigquery", _get_dialect_or_default())

    @patch("data_pipelines_cli.cli_commands.lint.BUILD_DIR", pathlib.Path("/a/b/c/d/e/f"))
    @patch("pathlib.Path.cwd", lambda: pathlib.Path("/a/b/c/d/e/f"))
    def test_default_dialect(self):
        self.assertEqual("ansi", _get_dialect_or_default())

    def test_get_source_tests_paths(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "pathlib.Path.cwd", lambda: pathlib.Path(tmp_dir)
        ):
            with open(goldens_dir_path.joinpath("dbt_project.yml"), "r") as orig_dbt, open(
                pathlib.Path(tmp_dir).joinpath("dbt_project.yml"), "w"
            ) as tmp_dbt:
                dbt_project = yaml.safe_load(orig_dbt)
                dbt_project["source-paths"] = ["models", "models2", "models3"]
                yaml.dump(dbt_project, tmp_dbt)

            self.assertSetEqual(
                {
                    pathlib.Path(tmp_dir).joinpath(dir_name)
                    for dir_name in ["models", "models2", "models3", "tests"]
                },
                set(_get_source_tests_paths()),
            )
