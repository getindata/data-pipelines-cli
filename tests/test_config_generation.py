import os
import pathlib
import unittest
from unittest.mock import patch

import yaml

import data_pipelines_cli.config_generation as cgen
from data_pipelines_cli.cli_constants import profiles_build_path


class TestConfigGeneration(unittest.TestCase):
    envs_to_test = [("dev", "bigquery"), ("test", "bigquery"), ("snow", "snowflake")]

    def setUp(self) -> None:
        self.maxDiff = None
        self.current_dir_path = pathlib.Path(__file__).parent

    def test_generation(self):
        for env, profile_type in self.envs_to_test:
            with self.subTest(env=env, profile_type=profile_type), patch(
                "data_pipelines_cli.cli_constants.BUILD_DIR", self.current_dir_path
            ), patch(
                "data_pipelines_cli.config_generation.BUILD_DIR",
                self.current_dir_path,
            ):

                cgen.generate_profiles_yml(env)
                self.profiles_path = profiles_build_path(env)

                with open(self.profiles_path, "r") as generated, open(
                    self.current_dir_path.joinpath(
                        "example_profiles", f"{env}_{profile_type}.yml"
                    ),
                    "r",
                ) as prepared:
                    self.assertDictEqual(
                        yaml.safe_load(generated), yaml.safe_load(prepared)
                    )

                os.remove(self.profiles_path)
                os.rmdir(self.profiles_path.parent)
                os.rmdir(self.profiles_path.parent.parent)
