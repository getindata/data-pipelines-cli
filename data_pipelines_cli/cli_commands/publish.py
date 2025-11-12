from __future__ import annotations

import json
import pathlib
import shutil
from typing import Any, Dict, List, Tuple

import click
import yaml

from ..cli_constants import BUILD_DIR
from ..cli_utils import echo_info, echo_warning
from ..config_generation import read_dictionary_from_config_directory
from ..data_structures import DbtModel, DbtSource, DbtTableColumn
from ..errors import DataPipelinesError

try:
    from git import Repo

    GIT_EXISTS = True
except ImportError:
    echo_warning("Git support not installed.")
    GIT_EXISTS = False


def _get_project_name_and_version() -> Tuple[str, str]:
    with open(pathlib.Path.cwd().joinpath("dbt_project.yml"), "r") as f:
        dbt_project_config = yaml.safe_load(f)
        return dbt_project_config["name"], dbt_project_config["version"]


def _get_database_and_schema_name(manifest_dict: Dict[str, Any]) -> Tuple[str, str]:
    nodes = manifest_dict.get("nodes")
    if not nodes:
        raise DataPipelinesError("Invalid manifest.json: missing 'nodes' key")

    for node_id, node in nodes.items():
        if node.get("resource_type") == "model":
            database = node.get("database")
            schema = node.get("schema")
            if not database or not schema:
                raise DataPipelinesError(
                    f"Model {node.get('name', node_id)} missing database or schema"
                )
            return database, schema

    raise DataPipelinesError("There is no model in 'manifest.json' file.")


def _parse_columns_dict_into_table_list(columns: Dict[str, Any]) -> List[DbtTableColumn]:
    return [
        DbtTableColumn(
            name=col_data.get("name", ""),
            description=col_data.get("description", ""),
            meta=col_data.get("meta", {}),
            quote=col_data.get("quote"),
            tags=col_data.get("tags", []),
        )
        for col_data in columns.values()
    ]


def _parse_models_schema(manifest_dict: Dict[str, Any]) -> List[DbtModel]:
    nodes = manifest_dict.get("nodes", {})
    models = []
    for node_id, node in nodes.items():
        if node.get("resource_type") == "model":
            models.append(
                DbtModel(
                    name=node.get("name", ""),
                    description=node.get("description", ""),
                    tags=node.get("tags", []),
                    meta=node.get("meta", {}),
                    columns=_parse_columns_dict_into_table_list(node.get("columns", {})),
                )
            )
    return models


def _get_dag_id() -> str:
    with open(BUILD_DIR.joinpath("dag", "config", "base", "airflow.yml"), "r") as airflow_yml:
        return yaml.safe_load(airflow_yml)["dag"]["dag_id"]


def _create_source(project_name: str) -> DbtSource:
    with open(pathlib.Path.cwd().joinpath("target", "manifest.json"), "r") as manifest_json:
        manifest_dict = json.load(manifest_json)

    database_name, schema_name = _get_database_and_schema_name(manifest_dict)

    return DbtSource(
        name=project_name,
        database=database_name,
        schema=schema_name,
        tables=_parse_models_schema(manifest_dict),
        meta={"dag": _get_dag_id()},
        tags=[f"project:{project_name}"],
    )


def _create_dbt_project(project_name: str, project_version: str) -> Dict[str, Any]:
    return {
        "name": f"{project_name}_sources",
        "source-paths": ["models"],
        "version": project_version,
        "config-version": 2,
    }


def create_package() -> pathlib.Path:
    """Create a dbt package out of the built project.

    :raises DataPipelinesError: There is no model in 'manifest.json' file.
    """
    project_name, project_version = _get_project_name_and_version()
    package_path = BUILD_DIR.joinpath("package")

    sources_path = package_path.joinpath("models", "sources.yml")
    sources_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sources_path, "w") as sources_yml:
        yaml.dump(
            {"version": 2, "sources": [_create_source(project_name)]},
            sources_yml,
            default_flow_style=False,
        )

    with open(package_path.joinpath("dbt_project.yml"), "w") as dbt_project_yml:
        yaml.dump(
            _create_dbt_project(project_name, project_version),
            dbt_project_yml,
            default_flow_style=False,
        )
    return package_path


def _clean_repo(packages_repo: pathlib.Path) -> None:
    if packages_repo.exists():
        echo_info(f"Removing {packages_repo}")
        shutil.rmtree(packages_repo)


def _copy_publication_to_repo(package_dest: pathlib.Path, package_path: pathlib.Path) -> None:
    if package_dest.exists():
        echo_info(f"Removing {package_dest}")
        shutil.rmtree(package_dest)
    echo_info("Copying new version")
    shutil.copytree(package_path, package_dest)


if GIT_EXISTS:

    def _configure_git_env(repo: Repo, config: Dict[str, Any]) -> None:
        repo.config_writer().set_value("user", "name", config["username"]).release()
        repo.config_writer().set_value("user", "email", config["email"]).release()

    def _commit_and_push_changes(repo: Repo, project_name: str, project_version: str) -> None:
        echo_info("Publishing")
        repo.git.add(all=True)
        repo.index.commit(f"Publication from project {project_name}, version: {project_version}")
        origin = repo.remote(name="origin")
        origin.push()


def publish_package(package_path: pathlib.Path, key_path: str, env: str) -> None:
    packages_repo = BUILD_DIR.joinpath("packages_repo")
    publish_config = read_dictionary_from_config_directory(
        BUILD_DIR.joinpath("dag"), env, "publish.yml"
    )
    _clean_repo(packages_repo)
    ssh_command_with_key = f"ssh -i {key_path}"
    repo = Repo.clone_from(
        publish_config["repository"],
        packages_repo,
        branch=publish_config["branch"],
        env={"GIT_SSH_COMMAND": ssh_command_with_key},
    )
    with repo.git.custom_environment(GIT_SSH_COMMAND=ssh_command_with_key):
        project_name, project_version = _get_project_name_and_version()
        _copy_publication_to_repo(packages_repo.joinpath(project_name), package_path)
        _configure_git_env(repo, publish_config)
        _commit_and_push_changes(repo, project_name, project_version)


@click.command(name="publish", help="Create a dbt package out of the project")
@click.option(
    "--key-path",
    type=str,
    required=True,
    help="Path to the key with write access to repo with published packages",
)
@click.option(
    "--env",
    default="base",
    type=str,
    show_default=True,
    required=True,
    help="Name of the environment",
)
def publish_command(key_path: str, env: str) -> None:
    package_path = create_package()
    publish_package(package_path, key_path, env)
