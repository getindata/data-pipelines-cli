import json
import pathlib
import shutil
import tempfile
import unittest
from os import PathLike
from typing import Any
from unittest.mock import MagicMock, patch

import yaml
from click.testing import CliRunner

from data_pipelines_cli.cli import _cli
from data_pipelines_cli.cli_commands.publish import (
    _create_source,
    _get_database_and_schema_name,
    _parse_columns_dict_into_table_list,
    _parse_models_schema,
    create_package,
)
from data_pipelines_cli.errors import DataPipelinesError

goldens_dir_path = pathlib.Path(__file__).parent.parent.joinpath("goldens")


class PublishCommandTestCase(unittest.TestCase):
    expected_sources = {
        "version": 2,
        "sources": [
            {
                "name": "my_test_project_1337",
                "database": "exampleproject",
                "schema": "username_private_working_dataset",
                "tags": ["project:my_test_project_1337"],
                "meta": {"dag": "experimental-dag"},
                "tables": [
                    {
                        "name": "my_first_dbt_model",
                        "description": "A starter dbt model",
                        "columns": [
                            {
                                "name": "id",
                                "description": "The primary key for this table",
                                "meta": {},
                                "quote": None,
                                "tags": [],
                            }
                        ],
                        "meta": {},
                        "tags": [],
                    },
                    {
                        "name": "my_second_dbt_model",
                        "description": "A starter dbt model",
                        "columns": [
                            {
                                "name": "id",
                                "description": "The primary key for this table",
                                "meta": {},
                                "quote": None,
                                "tags": [],
                            }
                        ],
                        "meta": {},
                        "tags": [],
                    },
                ],
            }
        ],
    }
    dbt_project = {
        "config-version": 2,
        "name": "my_test_project_1337_sources",
        "version": "1.2.3",
        "source-paths": ["models"],
    }

    def setUp(self) -> None:
        self.maxDiff = None

        self.build_temp_dir = pathlib.Path(tempfile.mkdtemp())
        dags_path = pathlib.Path(self.build_temp_dir).joinpath("dag")
        dags_path.mkdir(parents=True)
        shutil.copytree(goldens_dir_path.joinpath("config"), dags_path.joinpath("config"))

        profiles_yml_path = pathlib.Path(self.build_temp_dir).joinpath(
            "profiles", "env_execution", "profiles.yml"
        )
        profiles_yml_path.parent.mkdir(parents=True)
        shutil.copyfile(
            goldens_dir_path.joinpath("example_profiles", "dev_bigquery.yml"),
            profiles_yml_path,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.build_temp_dir)

    def mock_origin(self, name: str):
        self.origin = MagicMock()
        self.origin.push = MagicMock()
        return self.origin

    def mock_clone_from(self, url: PathLike, to_path: PathLike, **kwargs: Any):
        self.assertEqual("https://gitlab.com/getindata/dataops/some_repo.git", url)
        self.assertEqual("main", kwargs["branch"])

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
    def test_generate_correct_project(self):
        runner = CliRunner()
        with patch("data_pipelines_cli.cli_commands.publish.BUILD_DIR", self.build_temp_dir), patch(
            "data_pipelines_cli.config_generation.BUILD_DIR", self.build_temp_dir
        ), patch("data_pipelines_cli.cli_commands.publish.Repo", self.repo_class_mock()):
            runner.invoke(_cli, ["publish", "--key-path", "SOME_KEY.txt"])
            result = runner.invoke(_cli, ["publish", "--key-path", "SOME_KEY.txt"])

            self.verify_status_code(result)
            self.verify_publications()
            self.verify_generated_files()

    def verify_status_code(self, result):
        self.assertEqual(0, result.exit_code, msg=result.output)

    def verify_publications(self):
        self.git.add.assert_called_with(all=True)
        self.index.commit.assert_called_with(
            "Publication from project my_test_project_1337, version: 1.2.3"
        )
        self.origin.push.assert_called_with()

    def verify_generated_files(self):
        with open(
            pathlib.Path(self.build_temp_dir).joinpath("package", "models", "sources.yml"),
            "r",
        ) as sources_yml:
            self.assertDictEqual(self.expected_sources, yaml.safe_load(sources_yml))
        with open(
            pathlib.Path(self.build_temp_dir).joinpath("package", "dbt_project.yml"),
            "r",
        ) as dbt_project_yml:
            self.assertDictEqual(self.dbt_project, yaml.safe_load(dbt_project_yml))

    def test_no_models(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "pathlib.Path.cwd", lambda: pathlib.Path(tmp_dir)
        ):
            shutil.copyfile(
                goldens_dir_path.joinpath("dbt_project.yml"),
                pathlib.Path(tmp_dir).joinpath("dbt_project.yml"),
            )

            target_path = pathlib.Path(tmp_dir).joinpath("target")
            target_path.mkdir(parents=True)
            with open(
                goldens_dir_path.joinpath("target", "manifest.json"), "r"
            ) as manifest_json, open(target_path.joinpath("manifest.json"), "w") as tmp_manifest:
                manifest = json.load(manifest_json)
                for k in list(manifest["nodes"].keys()):
                    if k.startswith("model"):
                        del manifest["nodes"][k]
                json.dump(manifest, tmp_manifest)
            with self.assertRaises(DataPipelinesError):
                create_package()


class PublishManifestParsingTests(unittest.TestCase):
    """Unit tests for manifest dict parsing (post-refactor to remove dbt Python API)."""

    def setUp(self) -> None:
        self.maxDiff = None

    # P0: Critical Tests - Defensive Error Handling

    def test_get_db_schema_missing_nodes_key(self):
        """Validate error when manifest lacks 'nodes' key (line 33)."""
        manifest_no_nodes = {"metadata": {}, "sources": {}}
        with self.assertRaises(DataPipelinesError) as ctx:
            _get_database_and_schema_name(manifest_no_nodes)
        self.assertEqual("Invalid manifest.json: missing 'nodes' key", ctx.exception.message)

    def test_get_db_schema_model_missing_database(self):
        """Validate error when model lacks 'database' field (line 40)."""
        manifest = {
            "nodes": {
                "model.proj.broken_model": {
                    "resource_type": "model",
                    "name": "broken_model",
                    "schema": "public",
                    # Missing "database"
                }
            }
        }
        with self.assertRaises(DataPipelinesError) as ctx:
            _get_database_and_schema_name(manifest)
        self.assertIn("broken_model", ctx.exception.message)
        self.assertIn("missing database or schema", ctx.exception.message)

    def test_get_db_schema_model_missing_schema(self):
        """Validate error when model lacks 'schema' field (line 40)."""
        manifest = {
            "nodes": {
                "model.proj.broken_model": {
                    "resource_type": "model",
                    "name": "broken_model",
                    "database": "prod",
                    # Missing "schema"
                }
            }
        }
        with self.assertRaises(DataPipelinesError) as ctx:
            _get_database_and_schema_name(manifest)
        self.assertIn("broken_model", ctx.exception.message)
        self.assertIn("missing database or schema", ctx.exception.message)

    def test_get_db_schema_model_missing_name_fallback_to_node_id(self):
        """Validate fallback to node_id when model lacks 'name' field."""
        manifest = {
            "nodes": {
                "model.proj.unnamed_model": {
                    "resource_type": "model",
                    "database": "prod",
                    # Missing "schema" AND "name" - should use node_id
                }
            }
        }
        with self.assertRaises(DataPipelinesError) as ctx:
            _get_database_and_schema_name(manifest)
        self.assertIn("model.proj.unnamed_model", ctx.exception.message)

    def test_create_source_invalid_json(self):
        """Validate clear error when manifest.json contains invalid JSON."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = pathlib.Path(tmp_dir).joinpath("target")
            target_path.mkdir(parents=True)
            with open(target_path.joinpath("manifest.json"), "w") as f:
                f.write("{invalid json, missing quotes}")

            with patch("pathlib.Path.cwd", lambda: pathlib.Path(tmp_dir)):
                with self.assertRaises(json.JSONDecodeError):
                    _create_source("test_project")

    def test_create_source_file_not_found(self):
        """Validate clear error when manifest.json doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # target/ directory doesn't exist
            with patch("pathlib.Path.cwd", lambda: pathlib.Path(tmp_dir)):
                with self.assertRaises(FileNotFoundError):
                    _create_source("test_project")

    # P1: Important Tests - Real-World Scenarios

    def test_parse_model_with_full_metadata(self):
        """Validate parsing of models with tags, meta, and multiple columns."""
        manifest = {
            "nodes": {
                "model.proj.orders": {
                    "resource_type": "model",
                    "name": "orders",
                    "description": "Order fact table",
                    "database": "prod",
                    "schema": "analytics",
                    "tags": ["pii", "critical", "revenue"],
                    "meta": {"owner": "data-team", "sla_hours": 4},
                    "columns": {
                        "order_id": {
                            "name": "order_id",
                            "description": "Primary key",
                            "tags": ["pk"],
                            "meta": {"indexed": True},
                            "quote": True,
                        },
                        "customer_id": {
                            "name": "customer_id",
                            "description": "Foreign key",
                            "tags": ["fk", "pii"],
                            "meta": {},
                            "quote": False,
                        },
                        "amount": {
                            "name": "amount",
                            "description": "Order total",
                            "tags": [],
                            "meta": {},
                            "quote": None,
                        },
                    },
                }
            }
        }
        models = _parse_models_schema(manifest)
        self.assertEqual(1, len(models))
        self.assertEqual("orders", models[0]["name"])
        self.assertEqual(["pii", "critical", "revenue"], models[0]["tags"])
        self.assertEqual({"owner": "data-team", "sla_hours": 4}, models[0]["meta"])
        self.assertEqual(3, len(models[0]["columns"]))
        self.assertEqual(["pk"], models[0]["columns"][0]["tags"])
        self.assertTrue(models[0]["columns"][0]["quote"])
        self.assertFalse(models[0]["columns"][1]["quote"])
        self.assertIsNone(models[0]["columns"][2]["quote"])

    def test_parse_columns_empty_dict(self):
        """Validate models without columns return empty list."""
        columns = {}
        result = _parse_columns_dict_into_table_list(columns)
        self.assertEqual([], result)

    def test_parse_model_with_no_columns(self):
        """Validate models without documented columns are handled gracefully."""
        manifest = {
            "nodes": {
                "model.proj.undocumented": {
                    "resource_type": "model",
                    "name": "undocumented",
                    "description": "",
                    "database": "prod",
                    "schema": "staging",
                    "tags": [],
                    "meta": {},
                    "columns": {},
                }
            }
        }
        models = _parse_models_schema(manifest)
        self.assertEqual(1, len(models))
        self.assertEqual([], models[0]["columns"])

    def test_multiple_models_returns_first_match(self):
        """Validate behavior when manifest has multiple models."""
        manifest = {
            "nodes": {
                "model.proj.first": {
                    "resource_type": "model",
                    "name": "first",
                    "database": "db1",
                    "schema": "schema1",
                },
                "model.proj.second": {
                    "resource_type": "model",
                    "name": "second",
                    "database": "db2",
                    "schema": "schema2",
                },
            }
        }
        db, schema = _get_database_and_schema_name(manifest)
        # Note: Dict iteration order in Python 3.7+ is insertion-ordered
        # but manifest.json key order from dbt is undefined.
        # The function returns the FIRST model found.
        # We verify it returns ONE of the models (not both).
        self.assertIn(db, ["db1", "db2"])
        self.assertIn(schema, ["schema1", "schema2"])

    # P2: Nice-to-Have Tests - Edge Cases

    def test_column_missing_name_defaults_to_empty_string(self):
        """Validate column without 'name' field gets empty string default."""
        columns = {
            "col1": {
                "description": "Test column",
                "tags": ["test"],
                "meta": {},
                "quote": None,
                # Missing "name" field
            }
        }
        result = _parse_columns_dict_into_table_list(columns)
        self.assertEqual(1, len(result))
        self.assertEqual("", result[0]["name"])
        self.assertEqual("Test column", result[0]["description"])
        self.assertEqual(["test"], result[0]["tags"])

    def test_only_test_nodes_no_models(self):
        """Validate error when manifest has only test nodes (no models)."""
        manifest = {
            "nodes": {
                "test.proj.test_unique_id": {
                    "resource_type": "test",
                    "name": "test_unique_id",
                    "database": "prod",
                    "schema": "analytics",
                },
                "test.proj.test_not_null": {
                    "resource_type": "test",
                    "name": "test_not_null",
                    "database": "prod",
                    "schema": "analytics",
                },
            }
        }
        with self.assertRaises(DataPipelinesError) as ctx:
            _get_database_and_schema_name(manifest)
        self.assertIn("no model", ctx.exception.message.lower())

    def test_column_with_none_values(self):
        """Validate columns with None values are handled gracefully."""
        columns = {
            "col1": {
                "name": "test_col",
                "description": None,  # None instead of string
                "tags": None,  # None instead of list
                "meta": None,  # None instead of dict
                "quote": None,
            }
        }
        result = _parse_columns_dict_into_table_list(columns)
        self.assertEqual(1, len(result))
        self.assertEqual("test_col", result[0]["name"])
        # .get() with defaults should handle None by returning the default
        # But if the key exists with None, it returns None
        # This tests the actual behavior
        self.assertIsNone(result[0]["description"])
        self.assertIsNone(result[0]["tags"])
        self.assertIsNone(result[0]["meta"])
        self.assertIsNone(result[0]["quote"])

    def test_create_source_empty_manifest_file(self):
        """Validate error when manifest.json is empty."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = pathlib.Path(tmp_dir).joinpath("target")
            target_path.mkdir(parents=True)
            # Create empty file
            target_path.joinpath("manifest.json").touch()

            with patch("pathlib.Path.cwd", lambda: pathlib.Path(tmp_dir)):
                with self.assertRaises(json.JSONDecodeError):
                    _create_source("test_project")

    def test_model_with_empty_string_database(self):
        """Validate error when model has empty string for database."""
        manifest = {
            "nodes": {
                "model.proj.broken": {
                    "resource_type": "model",
                    "name": "broken",
                    "database": "",  # Empty string
                    "schema": "public",
                }
            }
        }
        with self.assertRaises(DataPipelinesError) as ctx:
            _get_database_and_schema_name(manifest)
        self.assertIn("broken", ctx.exception.message)
        self.assertIn("missing database or schema", ctx.exception.message)

    def test_model_with_empty_string_schema(self):
        """Validate error when model has empty string for schema."""
        manifest = {
            "nodes": {
                "model.proj.broken": {
                    "resource_type": "model",
                    "name": "broken",
                    "database": "prod",
                    "schema": "",  # Empty string
                }
            }
        }
        with self.assertRaises(DataPipelinesError) as ctx:
            _get_database_and_schema_name(manifest)
        self.assertIn("broken", ctx.exception.message)
        self.assertIn("missing database or schema", ctx.exception.message)

    def test_parse_schema_with_mixed_resource_types(self):
        """Validate correct filtering of models from mixed resource types."""
        manifest = {
            "nodes": {
                "model.proj.users": {
                    "resource_type": "model",
                    "name": "users",
                    "database": "prod",
                    "schema": "analytics",
                    "description": "Users table",
                    "tags": [],
                    "meta": {},
                    "columns": {},
                },
                "test.proj.test_users": {
                    "resource_type": "test",
                    "name": "test_users",
                    "database": "prod",
                    "schema": "analytics",
                },
                "seed.proj.countries": {
                    "resource_type": "seed",
                    "name": "countries",
                    "database": "prod",
                    "schema": "seed_data",
                },
                "model.proj.orders": {
                    "resource_type": "model",
                    "name": "orders",
                    "database": "prod",
                    "schema": "analytics",
                    "description": "Orders table",
                    "tags": [],
                    "meta": {},
                    "columns": {},
                },
            }
        }
        models = _parse_models_schema(manifest)
        # Should only return the 2 models, not test or seed
        self.assertEqual(2, len(models))
        model_names = [m["name"] for m in models]
        self.assertIn("users", model_names)
        self.assertIn("orders", model_names)
        self.assertNotIn("test_users", model_names)
        self.assertNotIn("countries", model_names)
