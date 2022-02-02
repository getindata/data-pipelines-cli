import os
import subprocess
import unittest
from io import StringIO
from unittest.mock import patch

from data_pipelines_cli.cli_utils import (
    echo_error,
    echo_info,
    echo_subinfo,
    echo_warning,
    get_argument_or_environment_variable,
    subprocess_run,
)
from data_pipelines_cli.errors import (
    DataPipelinesError,
    SubprocessNonZeroExitError,
    SubprocessNotFound,
)


class CliUtilsTest(unittest.TestCase):
    echo_is_printing_to_out = [
        (echo_error, False),
        (echo_warning, False),
        (echo_info, True),
        (echo_subinfo, True),
    ]

    def test_echoes_to_proper_streams(self):
        test_string = "Hello world!"
        endlined_test_string = test_string + "\n"

        for echo_fun, is_stdout in self.echo_is_printing_to_out:
            with self.subTest(function=echo_fun.__name__), patch(
                "sys.stdout", new=StringIO()
            ) as fake_out, patch("sys.stderr", new=StringIO()) as fake_err:
                echo_fun(test_string)
                self.assertEqual(endlined_test_string if is_stdout else "", fake_out.getvalue())
                self.assertEqual(endlined_test_string if not is_stdout else "", fake_err.getvalue())

    some_env_variable_key = "SOME_VARIABLE"
    some_env_variable_value = "some_value"

    @patch.dict(os.environ, {some_env_variable_key: some_env_variable_value})
    def test_get_argument_from_argument(self):
        argument = "argument"
        self.assertEqual(
            argument,
            get_argument_or_environment_variable(argument, "arg", self.some_env_variable_key),
        )

    @patch.dict(os.environ, {some_env_variable_key: some_env_variable_value})
    def test_get_argument_from_env_var(self):
        self.assertEqual(
            self.some_env_variable_value,
            get_argument_or_environment_variable(None, "arg", self.some_env_variable_key),
        )

    @patch.dict(os.environ, {})
    def test_get_argument_throw(self):
        with self.assertRaises(DataPipelinesError):
            get_argument_or_environment_variable(None, "arg", self.some_env_variable_key)

    @patch("data_pipelines_cli.cli_utils.subprocess.run")
    def test_subprocess_run_return_code(self, mock_run):
        mock_run.return_value.returncode = 0
        result = subprocess_run(["testproc", "--arg"])
        self.assertEqual(0, result.returncode)

    @patch("data_pipelines_cli.cli_utils.subprocess.run")
    def test_subprocess_run_not_exist(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        with self.assertRaises(SubprocessNotFound) as exc:
            _ = subprocess_run(["testproc", "--arg"])
        self.assertRegex(exc.exception.message, r"^testproc.*$")

    @patch("data_pipelines_cli.cli_utils.subprocess.run")
    def test_subprocess_run_nonzero_throws(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(21, cmd="")
        with self.assertRaises(SubprocessNonZeroExitError) as exc:
            _ = subprocess_run(["testproc", "--arg"])
        self.assertRegex(exc.exception.message, r"^testproc.*21$")
