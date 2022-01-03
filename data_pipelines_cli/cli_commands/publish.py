import glob
import pathlib
import shutil
from typing import Any, Dict, List, Tuple

import click
import yaml

from ..cli_constants import BUILD_DIR, PROFILE_NAME_ENV_EXECUTION
from ..cli_utils import echo_subinfo
from ..config_generation import get_profiles_yml_build_path
from ..data_structures import DbtModel, DbtSource
from ..dbt_utils import read_dbt_vars_from_configs
from ..errors import DataPipelinesError
from .prepare_env import replace_profiles_vars_with_values

DBT_DATABASE_KEY_BY_PROVIDER = {
    "bigquery": "project",
    "postgres": "dbname",
    "redshift": "dbname",
    "snowflake": "database",
}


def _get_project_name_and_version() -> Tuple[str, str]:
    with open(pathlib.Path.cwd().joinpath("dbt_project.yml"), "r") as f:
        dbt_project_config = yaml.safe_load(f)
        return dbt_project_config["name"], dbt_project_config["version"]


def _get_database_name(env: str) -> str:
    with open(
        get_profiles_yml_build_path(PROFILE_NAME_ENV_EXECUTION), "r"
    ) as profiles_yml:
        profiles_dict = replace_profiles_vars_with_values(
            yaml.safe_load(profiles_yml), read_dbt_vars_from_configs(env)
        )

    if len(profiles_dict) > 1:
        raise DataPipelinesError(
            "Generated 'profiles.yml' file has more than one profile listed."
        )

    profile_key = next(iter(profiles_dict))
    profile = profiles_dict[profile_key]
    profile_output = profile["outputs"][profile["target"]]
    return profile_output[DBT_DATABASE_KEY_BY_PROVIDER[profile_output["type"]]]


def _parse_models_schema() -> List[DbtModel]:
    with open(pathlib.Path.cwd().joinpath("dbt_project.yml"), "r") as f:
        dbt_project_config = yaml.safe_load(f)
        # TODO: in dbt 1.0 it is model-paths
        source_paths = dbt_project_config["source-paths"]

    models = []

    for source_path in source_paths:
        model_path = pathlib.Path.cwd().joinpath(source_path)

        # According to the dbt docs, 'schema.yml' does not have to be named 'schema'
        yml_files = glob.glob(str(model_path.joinpath("*.yml")))

        if len(yml_files) == 0:
            raise DataPipelinesError(f"No .yml file in {model_path}.")
        for schema_yml_name in yml_files:
            with open(schema_yml_name, "r") as schema_yml:
                echo_subinfo(f"Processing {schema_yml_name}.")
                models.extend(yaml.safe_load(schema_yml).get("models", iter(())))

    for model in models:
        for column in model.get("columns", iter(())):
            column.pop("tests", None)

    return models


def _get_dag_id() -> str:
    with open(
        BUILD_DIR.joinpath("dag", "config", "base", "airflow.yml"), "r"
    ) as airflow_yml:
        return yaml.safe_load(airflow_yml)["dag"]["dag_id"]


def _create_source(env: str) -> DbtSource:
    project_name, _ = _get_project_name_and_version()
    return DbtSource(
        name=project_name,
        database=_get_database_name(env),
        tables=_parse_models_schema(),
        meta={"dag": _get_dag_id()},
        tags=[f"project:{project_name}"],
    )


def _create_dbt_project() -> Dict[str, Any]:
    project_name, project_version = _get_project_name_and_version()
    return {
        "name": f"{project_name}_sources",
        "source-paths": ["models"],
        "version": project_version,
        "config-version": 2,
    }


def publish(env: str) -> None:
    package_path = BUILD_DIR.joinpath("package")

    sources_path = package_path.joinpath("models", "sources.yml")
    sources_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sources_path, "w") as sources_yml:
        yaml.dump({"version": 2, "sources": [_create_source(env)]}, sources_yml)

    for model_file in glob.glob(str(pathlib.Path.cwd().joinpath("models", "*.sql"))):
        model_file_name = package_path / "models" / pathlib.Path(model_file).name
        shutil.copyfile(model_file, model_file_name)

    with open(package_path.joinpath("dbt_project.yml"), "w") as dbt_project_yml:
        yaml.dump(_create_dbt_project(), dbt_project_yml)


@click.command(name="publish", help="Create a package out of the project")
@click.option("--env", required=True, default="base", help="Name of the environment")
def publish_command(env: str) -> None:
    publish(env)
