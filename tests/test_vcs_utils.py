import random
import string
import unittest

from data_pipelines_cli.vcs_utils import add_suffix_to_git_template_path


class GitSuffixTestCase(unittest.TestCase):
    remote_prefixes = ["git://", "git@", "git+", "http://", "https://"]

    def test_local_uri_not_has_git_suffix(self):
        for i in range(50):
            random_path = "".join(
                random.choices(string.ascii_letters + string.digits + "/", k=30)
            ).strip("/")

            with self.subTest(i=i, path=random_path):
                generated_path = add_suffix_to_git_template_path(random_path)
                self.assertFalse(generated_path.endswith(".git"))

    def test_remote_uri_has_git_suffix(self):
        for i in range(50):
            prefix = random.choice(self.remote_prefixes)
            random_path = "".join(
                random.choices(string.ascii_letters + string.digits + "/", k=30)
            ).strip("/")
            git_suffix = ".git" if bool(random.getrandbits(1)) else ""
            full_path = prefix + random_path + git_suffix

            with self.subTest(i=i, uri=full_path):
                generated_path = add_suffix_to_git_template_path(full_path)
                self.assertTrue(generated_path.endswith(".git"))
                self.assertFalse(generated_path.endswith(".git.git"))
