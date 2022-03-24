import json
import pathlib
import random
import shutil
import string
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import yaml
from click.testing import CliRunner

from data_pipelines_cli.cli import _cli
from data_pipelines_cli.cli_commands.generate.model_yaml import _is_ephemeral_model
from data_pipelines_cli.errors import DataPipelinesError

GOLDENS_DIR_PATH = pathlib.Path(__file__).parent.parent.joinpath("goldens")


@patch(
    "data_pipelines_cli.config_generation.get_profiles_dir_build_path",
    lambda *_args, **_kwargs: pathlib.Path("/a/b/c"),
)
class GenerateCommandTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.models_dir_path = pathlib.Path(tempfile.mkdtemp())
        random_dir_names = {
            "".join([random.choice(string.ascii_lowercase) for _ in range(random.randint(1, 10))])
            for _ in range(random.randint(1, 30))
        }
        self.overwritable_subdir_paths = set()
        self.subdir_paths = {
            self.models_dir_path.joinpath(subdir_name) for subdir_name in random_dir_names
        }

        overwritable_generated = False
        for subdir_path in self.subdir_paths:
            subdir_path.mkdir(parents=True)
            subdir_path.joinpath(f"{subdir_path.name}.sql").touch()
            if (not overwritable_generated) or random.randint(1, 6) == 1:
                subdir_path.joinpath(f"{subdir_path.name}.yml").touch()
                self.overwritable_subdir_paths.add(subdir_path)
                overwritable_generated = True

        self.dbt_command_args_tuples = []
        self.processed_models = set()

    def tearDown(self) -> None:
        shutil.rmtree(self.models_dir_path)

    def _mock_run_dbt_command(self, args_tuple, *_args, **_kwargs) -> str:
        self.dbt_command_args_tuples.append(args_tuple)
        # We are calling `dbt run-operation MACRO_NAME --args "{ARG_NAME: MODEL_NAME}"`
        # so to get MODEL_NAME out of the call one have to extract the first value
        # in the dictionary, without knowledge of the exact key (ARG_NAME)
        operation_args = yaml.safe_load(args_tuple[3])
        model_name = list(operation_args.values())[0]
        self.processed_models.add(model_name)
        return MagicMock(
            stdout=MagicMock(
                decode=lambda *a, **k: json.dumps(
                    {"code": "M011", "msg": yaml.dump({"models": [model_name]})}
                )
            )
        )

    def _mock_run_dbt_command_for_source(self, args_tuple, *_args, **_kwargs) -> str:
        self.dbt_command_args_tuples.append(args_tuple)
        # We are calling `dbt run-operation MACRO_NAME --args "{ARG_NAME: MODEL_NAME}"`
        # so to get MODEL_NAME out of the call one have to extract the first value
        # in the dictionary, without knowledge of the exact key (ARG_NAME)
        operation_args = yaml.safe_load(args_tuple[3])
        return MagicMock(
            stdout=MagicMock(
                decode=lambda *a, **k: json.dumps(
                    {"code": "M011", "msg": yaml.dump({"sources": [operation_args["schema_name"]]})}
                )
            )
        )

    def _mock_run_dbt_command_for_source_sql(self, args_tuple, *_args, **_kwargs) -> str:
        self.dbt_command_args_tuples.append(args_tuple)
        operation_args = yaml.safe_load(args_tuple[3])
        return MagicMock(
            stdout=MagicMock(
                decode=lambda *a, **k: json.dumps(
                    {
                        "code": "M011",
                        "msg": "SELECT * FROM "
                        f"{operation_args['source_name']}.{operation_args['table_name']}",
                    }
                )
            )
        )

    def test_generate_model_no_arg(self):
        runner = CliRunner()
        result = runner.invoke(_cli, ["generate", "model-yaml"])
        self.assertNotEqual(0, result.exit_code)
        self.assertIsInstance(result.exception, DataPipelinesError)

    def test_generate_source_no_arg(self):
        runner = CliRunner()
        result = runner.invoke(_cli, ["generate", "source-yaml"])
        self.assertNotEqual(0, result.exit_code)
        self.assertIsInstance(result.exception, DataPipelinesError)

    @patch("pathlib.Path.cwd", lambda: GOLDENS_DIR_PATH)
    @patch(
        "data_pipelines_cli.cli_commands.generate.model_yaml._is_ephemeral_model",
        lambda *args, **kwargs: False,
    )
    @patch(
        "data_pipelines_cli.cli_commands.generate.model_yaml.compile_project",
        lambda *_args, **_kwargs: None,
    )
    def test_generate_model_count_touched_subdirs(self):
        runner = CliRunner()
        with patch(
            "data_pipelines_cli.cli_commands.generate.utils.run_dbt_command",
            self._mock_run_dbt_command,
        ), runner.isolated_filesystem(temp_dir=self.models_dir_path.parent):
            result = runner.invoke(
                _cli,
                [
                    "generate",
                    "model-yaml",
                    str(self.models_dir_path),
                ],
            )
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertTrue(
                all(
                    args_tuple[1] == "generate_model_yaml"
                    for args_tuple in self.dbt_command_args_tuples
                )
            )

            self.assertSetEqual(
                {
                    path.stem
                    for path in self.subdir_paths.difference(self.overwritable_subdir_paths)
                },
                self.processed_models,
            )

    @patch("pathlib.Path.cwd", lambda: GOLDENS_DIR_PATH)
    @patch(
        "data_pipelines_cli.cli_commands.generate.model_yaml._is_ephemeral_model",
        lambda *args, **kwargs: False,
    )
    @patch(
        "data_pipelines_cli.cli_commands.generate.model_yaml.compile_project",
        lambda *_args, **_kwargs: None,
    )
    def test_generate_model_count_touched_subdirs_overwrite(self):
        runner = CliRunner()
        with patch(
            "data_pipelines_cli.cli_commands.generate.utils.run_dbt_command",
            self._mock_run_dbt_command,
        ), runner.isolated_filesystem(temp_dir=self.models_dir_path.parent):
            result = runner.invoke(
                _cli, ["generate", "model-yaml", "--overwrite", str(self.models_dir_path)]
            )
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertTrue(
                all(
                    args_tuple[1] == "generate_model_yaml"
                    for args_tuple in self.dbt_command_args_tuples
                )
            )
            self.assertSetEqual({path.stem for path in self.subdir_paths}, self.processed_models)

    @patch("pathlib.Path.cwd", lambda: GOLDENS_DIR_PATH)
    @patch(
        "data_pipelines_cli.cli_commands.generate.model_yaml._is_ephemeral_model",
        lambda *args, **kwargs: False,
    )
    @patch(
        "data_pipelines_cli.cli_commands.generate.model_yaml.compile_project",
        lambda *_args, **_kwargs: None,
    )
    def test_generate_model_count_touched_subdirs_with_meta(self):
        runner = CliRunner()
        with patch(
            "data_pipelines_cli.cli_commands.generate.utils.run_dbt_command",
            self._mock_run_dbt_command,
        ), runner.isolated_filesystem(temp_dir=self.models_dir_path.parent):
            result = runner.invoke(
                _cli, ["generate", "model-yaml", "--with-meta", str(self.models_dir_path)]
            )
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertTrue(
                all(
                    args_tuple[1] == "print_profile_schema"
                    for args_tuple in self.dbt_command_args_tuples
                )
            )
            self.assertSetEqual(
                {
                    path.stem
                    for path in self.subdir_paths.difference(self.overwritable_subdir_paths)
                },
                self.processed_models,
            )

    @patch("pathlib.Path.cwd", lambda: GOLDENS_DIR_PATH)
    @patch(
        "data_pipelines_cli.cli_commands.generate.model_yaml._is_ephemeral_model",
        lambda *args, **kwargs: False,
    )
    @patch(
        "data_pipelines_cli.cli_commands.generate.model_yaml.compile_project",
        lambda *_args, **_kwargs: None,
    )
    def test_generate_model_count_touched_subdirs_with_meta_overwrite(self):
        runner = CliRunner()
        with patch(
            "data_pipelines_cli.cli_commands.generate.utils.run_dbt_command",
            self._mock_run_dbt_command,
        ), runner.isolated_filesystem(temp_dir=self.models_dir_path.parent):
            result = runner.invoke(
                _cli,
                ["generate", "model-yaml", "--with-meta", "--overwrite", str(self.models_dir_path)],
            )
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertTrue(
                all(
                    args_tuple[1] == "print_profile_schema"
                    for args_tuple in self.dbt_command_args_tuples
                )
            )
            self.assertSetEqual({path.stem for path in self.subdir_paths}, self.processed_models)

    @patch(
        "data_pipelines_cli.cli_commands.generate.source_yaml.generate_profiles_yml",
        lambda *_args, **_kwargs: pathlib.Path("/a/b/c"),
    )
    def test_generate_source_yaml(self):
        runner = CliRunner()
        with patch(
            "data_pipelines_cli.cli_commands.generate.utils.run_dbt_command",
            self._mock_run_dbt_command_for_source,
        ), runner.isolated_filesystem(temp_dir=self.models_dir_path.parent):
            result = runner.invoke(
                _cli,
                [
                    "generate",
                    "source-yaml",
                    "--source-path",
                    self.models_dir_path,
                    "dataset1",
                    "dataset2",
                    "dataset3",
                ],
            )
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertTrue(
                all(
                    args_tuple[1] == "generate_source"
                    for args_tuple in self.dbt_command_args_tuples
                )
            )
            with open(
                self.models_dir_path.joinpath(f"{self.models_dir_path.stem}.yml"), "r"
            ) as source_yml:
                self.assertDictEqual(
                    {"version": 2, "sources": ["dataset1", "dataset2", "dataset3"]},
                    yaml.safe_load(source_yml),
                )

    @patch(
        "data_pipelines_cli.cli_commands.generate.source_sql.generate_profiles_yml",
        lambda *_args, **_kwargs: pathlib.Path("/a/b/c"),
    )
    def test_generate_source_sql(self):
        runner = CliRunner()
        with patch(
            "data_pipelines_cli.cli_commands.generate.utils.run_dbt_command",
            self._mock_run_dbt_command_for_source_sql,
        ), runner.isolated_filesystem(temp_dir=self.models_dir_path.parent):
            result = runner.invoke(
                _cli,
                [
                    "generate",
                    "source-sql",
                    "--source-yaml-path",
                    GOLDENS_DIR_PATH.joinpath("source_yaml.yml"),
                    "--staging-path",
                    self.models_dir_path.joinpath("s_t_a_ging"),
                ],
            )
            self.assertEqual(0, result.exit_code, msg=result.exception)
            self.assertTrue(
                all(
                    args_tuple[1] == "generate_base_model"
                    for args_tuple in self.dbt_command_args_tuples
                )
            )
            for source_name, table_name in [
                ("source1", "table1"),
                ("source1", "table2"),
                ("source2", "table1"),
            ]:
                with open(
                    self.models_dir_path.joinpath(
                        "s_t_a_ging", source_name, f"stg_{table_name}.sql"
                    ),
                    "r",
                ) as table_yml:
                    self.assertEqual(f"SELECT * FROM {source_name}.{table_name}", table_yml.read())

    def test_is_ephemeral_model(self):
        example_dict = {
            "nodes": {
                "a": {"name": "a", "config": {"materialized": "table"}},
                "b": {"name": "b", "config": {"materialized": "ephemeral"}},
                "c": {"name": "c", "config": {"materialized": "view"}},
            }
        }
        self.assertFalse(_is_ephemeral_model(example_dict, "a"))
        self.assertTrue(_is_ephemeral_model(example_dict, "b"))
        self.assertFalse(_is_ephemeral_model(example_dict, "c"))
        with self.assertRaises(DataPipelinesError):
            _is_ephemeral_model(example_dict, "d")
