import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import yaml

import data_pipelines_cli.config_generation as cgen


def _noop():
    pass


class TestConfigGeneration(unittest.TestCase):
    envs_to_test = [
        ("dev", "bigquery"),
        ("staging", "bigquery"),
        ("local", "snowflake"),
    ]
    configs_to_test = {
        "dev": {
            "target": "env_execution",
            "target_type": "bigquery",
            "vars": {
                "variable_1": 123,
                "variable_2": "var2",
            },
        },
        "local": {
            "target": "local",
            "target_type": "snowflake",
            "vars": {
                "variable_1": 123,
                "variable_2": "var2",
            },
        },
        "staging": {
            "target": "env_execution",
            "target_type": "bigquery",
            "vars": {
                "variable_1": 1337,
                "variable_2": "var21",
            },
        },
    }

    def setUp(self) -> None:
        self.maxDiff = None
        self.goldens_dir_path = pathlib.Path(__file__).parent.joinpath("goldens")

    def test_copy_dag_dir(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "data_pipelines_cli.config_generation.BUILD_DIR", pathlib.Path(tmp_dir)
        ), patch("pathlib.Path.cwd", lambda: self.goldens_dir_path):
            cgen.copy_dag_dir_to_build_dir()
            tmp_dag_dir = pathlib.Path(tmp_dir).joinpath("dag")
            self.assertEqual(2, len(os.listdir(tmp_dag_dir)))
            with open(tmp_dag_dir.joinpath("a.txt"), "r") as f:
                self.assertEqual("abcdef", f.read())
            with open(tmp_dag_dir.joinpath("b.txt"), "r") as f:
                self.assertEqual("123456", f.read())

    def test_copy_dir_rmdir_if_exists(self):
        with tempfile.TemporaryDirectory() as tmp_dir1, tempfile.TemporaryDirectory() as tmp_dir2:  # noqa: E501
            path1 = pathlib.Path(tmp_dir2)
            with open(path1.joinpath("a.txt"), "w") as f:
                f.write("qwerty987")
            path1.joinpath("b.txt").touch()
            self.assertEqual(2, len(os.listdir(path1)))

            path2 = pathlib.Path(tmp_dir1)
            with open(path2.joinpath("a.txt"), "w") as f:
                f.write("abc1234")
            path2.joinpath("b.txt").touch()
            path2.joinpath("c.txt").touch()
            self.assertEqual(3, len(os.listdir(path2)))
            with open(path2.joinpath("a.txt"), "r") as f:
                self.assertEqual("abc1234", f.read())

            cgen._copy_src_dir_to_dst_dir(path1, path2)

            self.assertEqual(2, len(os.listdir(path2)))
            with open(path2.joinpath("a.txt"), "r") as f:
                self.assertEqual("qwerty987", f.read())

    def test_read_from_config_dir(self):
        for env, _ in self.envs_to_test:
            with self.subTest(env=env):
                self.assertDictEqual(
                    self.configs_to_test[env],
                    cgen.read_dictionary_from_config_directory(
                        self.goldens_dir_path, env, "dbt.yml"
                    ),
                )

    def test_generation(self):
        for env, profile_type in self.envs_to_test:
            with self.subTest(
                env=env, profile_type=profile_type
            ), tempfile.TemporaryDirectory() as tmp_dir, patch(
                "data_pipelines_cli.cli_constants.BUILD_DIR", pathlib.Path(tmp_dir)
            ), patch(
                "data_pipelines_cli.config_generation.BUILD_DIR",
                pathlib.Path(tmp_dir),
            ), patch(
                "pathlib.Path.cwd", lambda: self.goldens_dir_path
            ):
                self.profiles_path = cgen.generate_profiles_yml(env).joinpath("profiles.yml")
                with open(self.profiles_path, "r") as generated, open(
                    self.goldens_dir_path.joinpath("example_profiles", f"{env}_{profile_type}.yml"),
                    "r",
                ) as prepared:
                    self.assertDictEqual(yaml.safe_load(prepared), yaml.safe_load(generated))

                os.remove(self.profiles_path)
                os.rmdir(self.profiles_path.parent)
                os.rmdir(self.profiles_path.parent.parent)
