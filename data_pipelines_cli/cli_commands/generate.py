import json
import pathlib
import re
import sys
from typing import Any, Dict, Optional, Sequence

import click
import yaml

from ..cli_utils import echo_info, echo_warning
from ..config_generation import generate_profiles_yml, get_profiles_dir_build_path
from ..dbt_utils import run_dbt_command
from ..errors import DataPipelinesError, SubprocessNonZeroExitError
from .compile import compile_project

if sys.version_info >= (3, 8):
    from typing import TypedDict  # pylint: disable=no-name-in-module
else:
    from typing_extensions import TypedDict


class MacroArgName(TypedDict):
    deps_name: str
    macro_name: str
    arg_name: str


def _get_deps_macro_and_arg_name(with_meta: bool) -> MacroArgName:
    return (
        MacroArgName(
            deps_name="dbt_profiler", macro_name="print_profile_schema", arg_name="relation_name"
        )
        if with_meta
        else MacroArgName(
            deps_name="codegen", macro_name="generate_model_yaml", arg_name="model_name"
        )
    )


def _get_unfiltered_macro_run_output(
    env: str, macro_name: str, macro_args: Dict[str, str], profiles_path: pathlib.Path
) -> str:
    print_args = yaml.dump(macro_args, default_flow_style=True, width=sys.maxsize).rstrip()
    dbt_command_result_bytes = run_dbt_command(
        ("run-operation", macro_name, "--args", print_args),
        env,
        profiles_path,
        capture_output=True,
    )
    return dbt_command_result_bytes.stdout.decode(encoding=sys.stdout.encoding or "utf-8")


def _filter_out_dbt_log_output(raw_dbt_output: str) -> str:
    pattern = re.compile(r"\d{2}:\d{2}:\d{2}.*")
    return "\n".join(filter(lambda line: not re.match(pattern, line), raw_dbt_output.splitlines()))


def _run_and_filter_dbt_macro(
    env: str, macro_name: str, macro_args: Dict[str, Any], profiles_path: pathlib.Path
) -> str:
    schema_output = _get_unfiltered_macro_run_output(env, macro_name, macro_args, profiles_path)
    return _filter_out_dbt_log_output(schema_output)


def _generate_models_or_sources_from_single_table(
    env: str, macro_name: str, macro_args: Dict[str, Any], profiles_path: pathlib.Path
) -> Dict[str, Any]:
    return yaml.safe_load(_run_and_filter_dbt_macro(env, macro_name, macro_args, profiles_path))


def _is_ephemeral_model(manifest: Dict[str, Any], model_name: str) -> bool:
    for node in manifest["nodes"].values():
        if node["name"] == model_name:
            return node["config"]["materialized"] == "ephemeral"
    raise DataPipelinesError(f"Could not find {model_name} in project's 'manifest.json' file.")


def _get_output_file_or_warn_if_exists(
    directory: pathlib.Path, overwrite: bool, file_extension: str, filename: Optional[str] = None
) -> Optional[pathlib.Path]:
    output_path = directory.joinpath(f"{filename or directory.name}.{file_extension}")
    if output_path.exists():
        if not overwrite:
            echo_warning(
                f"{str(output_path)} in directory {str(directory)} exists, it "
                "will not be overwritten. If you want to overwrite it, pass "
                "'--overwrite' flag."
            )
            return None
        else:
            echo_warning(
                f"{str(output_path)} in directory {str(directory)} exists, it gets overwritten."
            )
    return output_path


def _generate_model_yamls_for_directory(
    directory: pathlib.Path,
    env: str,
    overwrite: bool,
    macro_arg_name: MacroArgName,
    profiles_path: pathlib.Path,
) -> None:
    output_path = _get_output_file_or_warn_if_exists(directory, overwrite, "yml")
    if output_path is None:
        return

    click.echo(f"Generating schema file for directory: {str(directory)}")
    with open(pathlib.Path.cwd().joinpath("target", "manifest.json"), "r") as manifest_json:
        manifest = json.load(manifest_json)
    models = [
        model
        for file in directory.glob("*.sql")
        if not _is_ephemeral_model(manifest, file.stem)
        for model in _generate_models_or_sources_from_single_table(
            env,
            macro_arg_name["macro_name"],
            {macro_arg_name["arg_name"]: file.stem},
            profiles_path,
        )["models"]
    ]
    if len(models) == 0:
        echo_warning(
            f"{str(directory)} does not have any models. Schema file will not be generated."
        )
    else:
        with open(output_path, "w") as output_file:
            yaml.dump({"version": 2, "models": models}, output_file, default_flow_style=False)
        echo_info(f"Generated source schema file and saved in {output_path}")


def generate_model_yamls(
    env: str, with_meta: bool, overwrite: bool, model_paths: Sequence[pathlib.Path]
) -> None:
    compile_project(env)
    profiles_path = get_profiles_dir_build_path(env)

    macro_arg_name = _get_deps_macro_and_arg_name(with_meta)
    echo_info(f"Generating schema files for directories: {' '.join(map(str, model_paths))}")
    try:
        for paths in model_paths:
            for subdir in paths.glob("**/"):
                _generate_model_yamls_for_directory(
                    subdir, env, overwrite, macro_arg_name, profiles_path
                )
    except SubprocessNonZeroExitError as err:
        raise DataPipelinesError(
            "Error while running dbt command. Ensure that you have "
            f"{macro_arg_name['deps_name']} installed and you have chosen correct models to "
            "generate schema.yml out of.\n" + err.message,
            submessage=err.submessage,
        )


def generate_source_yamls(
    env: str, source_path: pathlib.Path, overwrite: bool, schema_names: Sequence[str]
) -> None:
    profiles_path = generate_profiles_yml(env)
    output_path = _get_output_file_or_warn_if_exists(source_path, overwrite, "yml")
    if output_path is None:
        return
    source_path.mkdir(parents=True, exist_ok=True)

    try:
        sources = [
            source
            for schema in schema_names
            for source in _generate_models_or_sources_from_single_table(
                env,
                "generate_source",
                {"schema_name": schema, "generate_columns": True},
                profiles_path,
            )["sources"]
        ]
        with open(output_path, "w") as output_file:
            yaml.dump({"version": 2, "sources": sources}, output_file, default_flow_style=False)
        echo_info(f"Generated source schema file and saved in {output_path}")
    except SubprocessNonZeroExitError as err:
        raise DataPipelinesError(
            "Error while running dbt command. Ensure that you have codegen "
            "installed and you have chosen correct existing datasets (schemas) to "
            "generate source.yml out of.\n" + err.message,
            submessage=err.submessage,
        )


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
            output_path = _get_output_file_or_warn_if_exists(
                staging_path, overwrite, "sql", f"{table_name}"
            )
            if output_path is None:
                continue
            table_sql = _run_and_filter_dbt_macro(
                env,
                "generate_base_model",
                {"source_name": source_name, "table_name": table_name},
                profiles_path,
            )
            with open(output_path, "w") as output:
                output.write(table_sql)
    except SubprocessNonZeroExitError as err:
        raise DataPipelinesError(
            "Error while running dbt command. Ensure that you have codegen "
            "installed and you have chosen correct existing sources to "
            "generate table sqls out of.\n" + err.message,
            submessage=err.submessage,
        )


# -------------------------------- COMMANDS -----------------------------------
@click.group(name="generate", help="Generate additional dbt files")
def generate_group() -> None:
    pass


@generate_group.command(
    name="model-yaml", help="Generate schema YAML using codegen or dbt-profiler"
)
@click.option("--env", default="local", type=str, help="Name of the environment", show_default=True)
@click.option(
    "--with-meta", type=bool, is_flag=True, help="Whether to generate dbt-profiler metadata"
)
@click.option(
    "--overwrite", type=bool, is_flag=True, help="Whether to overwrite existing YAML files"
)
@click.argument(
    "model-path",
    type=click.Path(exists=True, path_type=pathlib.Path, file_okay=False, dir_okay=True),
    nargs=-1,
)
def _generate_model_yaml_command(
    env: str, with_meta: bool, overwrite: bool, model_path: Sequence[pathlib.Path]
) -> None:
    if len(model_path) == 0:
        raise DataPipelinesError("Command expects at least one 'model-path' argument")
    generate_model_yamls(env, with_meta, overwrite, model_path)


@generate_group.command(name="source-yaml", help="Generate source YAML using codegen")
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
def _generate_source_command(
    env: str, source_path: pathlib.Path, overwrite: bool, schema_name: Sequence[str]
) -> None:
    if len(schema_name) == 0:
        raise DataPipelinesError("Command expects at least one 'schema-name' argument")
    generate_source_yamls(env, source_path, overwrite, schema_name)


@generate_group.command(
    name="source-sql", help="Generate SQLs that represents tables in given dataset"
)
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
def _generate_source_sqls(
    env: str, source_yaml_path: pathlib.Path, staging_path: pathlib.Path, overwrite: bool
) -> None:
    generate_source_sqls(env, source_yaml_path, staging_path, overwrite)
