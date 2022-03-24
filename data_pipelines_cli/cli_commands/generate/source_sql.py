import pathlib

import click
import yaml

from ...config_generation import generate_profiles_yml
from ...errors import DataPipelinesError, SubprocessNonZeroExitError
from .utils import get_macro_run_output, get_output_file_or_warn_if_exists


def generate_source_sqls(
    env: str, source_yaml_path: pathlib.Path, staging_path: pathlib.Path, overwrite: bool
) -> None:
    profiles_path = generate_profiles_yml(env)
    staging_path.mkdir(parents=True, exist_ok=True)
    with open(source_yaml_path, "r") as source_yaml:
        source_dict = yaml.safe_load(source_yaml)
        tables_by_source = [
            (source["name"], table["name"])
            for source in source_dict["sources"]
            for table in source["tables"]
        ]
    try:
        for source_name, table_name in tables_by_source:
            output_path = get_output_file_or_warn_if_exists(
                staging_path.joinpath(source_name), overwrite, "sql", f"stg_{table_name}"
            )
            if output_path is None:
                continue
            table_sql = get_macro_run_output(
                env,
                "generate_base_model",
                {"source_name": source_name, "table_name": table_name},
                profiles_path,
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as output:
                output.write(table_sql)
    except SubprocessNonZeroExitError as err:
        raise DataPipelinesError(
            "Error while running dbt command. Ensure that you have codegen "
            "installed and you have chosen correct existing sources to "
            "generate table sqls out of.\n" + err.message,
            submessage=err.submessage,
        )


@click.command(name="source-sql", help="Generate SQLs that represents tables in given dataset")
@click.option("--env", default="local", type=str, help="Name of the environment", show_default=True)
@click.option(
    "--source-yaml-path",
    type=click.Path(exists=True, path_type=pathlib.Path, file_okay=True),
    default=pathlib.Path.cwd().joinpath("models", "source", "source.yml"),
    show_default=True,
    help="Path to the 'source.yml' schema file",
    required=True,
)
@click.option(
    "--staging-path",
    default=pathlib.Path.cwd().joinpath("models", "staging"),
    show_default=True,
    type=pathlib.Path,
    help="Path to the 'staging' directory",
    required=True,
)
@click.option(
    "--overwrite", type=bool, is_flag=True, help="Whether to overwrite existing SQL files"
)
def generate_source_sqls_command(
    env: str, source_yaml_path: pathlib.Path, staging_path: pathlib.Path, overwrite: bool
) -> None:
    generate_source_sqls(env, source_yaml_path, staging_path, overwrite)
