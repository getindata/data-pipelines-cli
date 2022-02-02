import pathlib
import subprocess
import tempfile
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from data_pipelines_cli.io_utils import git_revision_hash, replace


class TestReplace(unittest.TestCase):
    pattern_to_replace = "<(TEST-PaTtErN___!@#$%^abcdef__"
    regex_to_replace = r"<\(TEST-PaTtErN___!@#\$%\^[a-z]+__"
    replacement = "0x13370x42  ||  http://example,com<>"
    text_to_replace = (
        f'<(TEST-Pattern,1234{pattern_to_replace}>>>>=><><"\n\n{pattern_to_replace}xxx'
    )
    expected_result = f'<(TEST-Pattern,1234{replacement}>>>>=><><"\n\n{replacement}xxx'

    def test_replace(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filename = pathlib.Path(tmp_dir).joinpath("test")
            with open(filename, "w") as tmp_file:
                tmp_file.write(self.text_to_replace)
            replace(tmp_file.name, self.regex_to_replace, self.replacement)
            with open(filename, "r") as tmp_file:
                output = tmp_file.readlines()
                self.assertEqual(self.expected_result, "".join(output))


class TestGitRevisionHash(unittest.TestCase):
    @patch("data_pipelines_cli.io_utils.subprocess.run")
    def test_git_revision_hash(self, mock_run):
        git_sha = "abcdef1337"

        mock_stdout = MagicMock()
        mock_stdout.configure_mock(**{"stdout.decode.return_value": git_sha})
        mock_run.return_value = mock_stdout

        result = git_revision_hash()
        self.assertEqual(git_sha, result)

    @patch("data_pipelines_cli.io_utils.subprocess.run")
    def test_git_does_not_exist(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        result = git_revision_hash()
        self.assertEqual(None, result)

    @patch("data_pipelines_cli.io_utils.subprocess.run")
    def test_git_error(self, mock_run):
        test_error = "Some test error"
        mock_run.side_effect = subprocess.CalledProcessError(128, cmd="", stderr=test_error)

        with patch("sys.stderr", new=StringIO()) as fake_out:
            result = git_revision_hash()
            self.assertEqual(None, result)
            self.assertIn(test_error, fake_out.getvalue())
