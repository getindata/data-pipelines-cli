import json
import pathlib
from typing import Any, Dict, List, Tuple, cast

import click
import yaml
from dbt.contracts.graph.manifest import Manifest, ManifestNode
from dbt.contracts.graph.parsed import ColumnInfo

from ..cli_constants import BUILD_DIR
from ..data_structures import DbtModel, DbtSource, DbtTableColumn
from ..errors import DataPipelinesError


def _get_project_name_and_version() -> Tuple[str, str]:
    with open(pathlib.Path.cwd().joinpath("dbt_project.yml"), "r") as f:
        dbt_project_config = yaml.safe_load(f)
        return dbt_project_config["name"], dbt_project_config["version"]


def _get_database_and_schema_name(manifest: Manifest) -> Tuple[str, str]:
    try:
        model = next(
            node
            for node in map(lambda n: cast(ManifestNode, n), manifest.nodes.values())
            if node.resource_type == "model"
        )
        return model.database, model.schema
    except StopIteration:
        raise DataPipelinesError("There is no model in 'manifest.json' file.")


def _parse_columns_dict_into_table_list(
    columns: Dict[str, ColumnInfo]
) -> List[DbtTableColumn]:
    return [
        DbtTableColumn(
            name=column.name,
            description=column.description,
            meta=column.meta,
            quote=column.quote,
            tags=column.tags,
        )
        for column in columns.values()
    ]


def _parse_models_schema(manifest: Manifest) -> List[DbtModel]:
    return [
        DbtModel(
            name=node.name,
            description=node.description,
            tags=node.tags,
            meta=node.meta,
            columns=_parse_columns_dict_into_table_list(node.columns),
        )
        for node in map(lambda n: cast(ManifestNode, n), manifest.nodes.values())
        if node.resource_type == "model"
    ]


def _get_dag_id() -> str:
    with open(
        BUILD_DIR.joinpath("dag", "config", "base", "airflow.yml"), "r"
    ) as airflow_yml:
        return yaml.safe_load(airflow_yml)["dag"]["dag_id"]


def _create_source(project_name: str) -> DbtSource:
    with open(
        pathlib.Path.cwd().joinpath("target", "manifest.json"), "r"
    ) as manifest_json:
        manifest_dict = json.load(manifest_json)
        manifest = Manifest.from_dict(manifest_dict)

    database_name, schema_name = _get_database_and_schema_name(manifest)

    return DbtSource(
        name=project_name,
        database=database_name,
        schema=schema_name,
        tables=_parse_models_schema(manifest),
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


def publish() -> None:
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


@click.command(name="publish", help="Create a dbt package out of the project")
def publish_command() -> None:
    publish()
