import pathlib
from typing import Sequence

import click
import yaml

from ...cli_utils import echo_info
from ...config_generation import generate_profiles_yml
from ...errors import DataPipelinesError, SubprocessNonZeroExitError
from ..generate.utils import (
    generate_models_or_sources_from_single_table,
    get_output_file_or_warn_if_exists,
)


def generate_source_yamls(
    env: str, source_path: pathlib.Path, overwrite: bool, schema_names: Sequence[str]
) -> None:
    profiles_path = generate_profiles_yml(env)
    output_path = get_output_file_or_warn_if_exists(source_path, overwrite, "yml")
    if output_path is None:
        return
    source_path.mkdir(parents=True, exist_ok=True)

    try:
        sources = [
            source
            for schema in schema_names
            for source in generate_models_or_sources_from_single_table(
                env,
                "generate_source",
                {"schema_name": schema, "generate_columns": True, "include_descriptions": True},
                profiles_path,
            )["sources"]
        ]
        with open(output_path, "w") as output_file:
            yaml.dump(
                {"version": 2, "sources": sources},
                output_file,
                default_flow_style=False,
                sort_keys=False,
            )
        echo_info(f"Generated source schema file and saved in {output_path}")
    except SubprocessNonZeroExitError as err:
        raise DataPipelinesError(
            "Error while running dbt command. Ensure that you have codegen "
            "installed and you have chosen correct existing datasets (schemas) to "
            "generate source.yml out of.\n" + err.message,
            submessage=err.submessage,
        )


@click.command(name="source-yaml", help="Generate source YAML using codegen")
@click.option("--env", default="local", type=str, help="Name of the environment", show_default=True)
@click.option(
    "--source-path",
    default=pathlib.Path.cwd().joinpath("models", "source"),
    show_default=True,
    type=pathlib.Path,
    help="Path to the 'source' directory",
    required=True,
)
@click.option(
    "--overwrite", type=bool, is_flag=True, help="Whether to overwrite an existing YAML file"
)
@click.argument("schema-name", type=str, nargs=-1)
def generate_source_yamls_command(
    env: str, source_path: pathlib.Path, overwrite: bool, schema_name: Sequence[str]
) -> None:
    if len(schema_name) == 0:
        raise DataPipelinesError("Command expects at least one 'schema-name' argument")
    generate_source_yamls(env, source_path, overwrite, schema_name)
