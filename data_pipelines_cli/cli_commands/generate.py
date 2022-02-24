import json
import pathlib
import re
import sys
from typing import Any, Dict, List, Sequence

import click
import yaml

from ..cli_utils import echo_info, echo_warning
from ..config_generation import get_profiles_dir_build_path
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
    env: str, model_name: str, macro_name: str, arg_name: str, profiles_path: pathlib.Path
) -> str:
    print_args = yaml.dump(
        {arg_name: model_name}, default_flow_style=True, width=sys.maxsize
    ).rstrip()
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


def _generate_models_from_single_table(
    env: str, model_name: str, macro_name: str, arg_name: str, profiles_path: pathlib.Path
) -> List[Dict[str, Any]]:

    schema_output = _get_unfiltered_macro_run_output(
        env, model_name, macro_name, arg_name, profiles_path
    )
    filtered_output = _filter_out_dbt_log_output(schema_output)
    return yaml.safe_load(filtered_output)["models"]


def _is_ephemeral_model(manifest: Dict[str, Any], model_name: str) -> bool:
    for node in manifest["nodes"].values():
        if node["name"] == model_name:
            return node["config"]["materialized"] == "ephemeral"
    raise DataPipelinesError(f"Could not find {model_name} in project's 'manifest.json' file.")


def _generate_model_yamls_for_directory(
    directory: pathlib.Path,
    env: str,
    overwrite: bool,
    macro_arg_name: MacroArgName,
    profiles_path: pathlib.Path,
) -> None:
    output_path = directory.joinpath(f"{directory.name}.yml")

    if output_path.exists():
        if not overwrite:
            echo_warning(
                f"{str(output_path)} in directory {str(directory)} exists, it "
                "will not be overwritten. If you want to overwrite it, pass "
                "'--overwrite' flag."
            )
            return
        else:
            echo_warning(
                f"{str(output_path)} in directory {str(directory)} exists, it gets overwritten."
            )

    click.echo(f"Generating schema file for directory: {str(directory)}")
    with open(pathlib.Path.cwd().joinpath("target", "manifest.json"), "r") as manifest_json:
        manifest = json.load(manifest_json)
    models = [
        model
        for file in directory.glob("*.sql")
        if not _is_ephemeral_model(manifest, file.stem)
        for model in _generate_models_from_single_table(
            env, file.stem, macro_arg_name["macro_name"], macro_arg_name["arg_name"], profiles_path
        )
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


@click.group(name="generate", help="Generate additional dbt files")
def generate_group() -> None:
    pass


@generate_group.command(
    name="model-yaml", help="Generate schema YAML using codegen or dbt-profiler"
)
@click.option("--env", default="local", type=str, help="Name of the environment")
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


@generate_group.command(name="source", help="")
def _generate_source_command(env: str, output: str, table: Sequence[str]) -> None:
    pass
