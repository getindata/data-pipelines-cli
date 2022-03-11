import pathlib
import re
import sys
from typing import Any, Dict, Optional

import yaml

from ...cli_utils import echo_warning
from ...dbt_utils import run_dbt_command


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


def run_and_filter_dbt_macro(
    env: str, macro_name: str, macro_args: Dict[str, Any], profiles_path: pathlib.Path
) -> str:
    schema_output = _get_unfiltered_macro_run_output(env, macro_name, macro_args, profiles_path)
    return _filter_out_dbt_log_output(schema_output)


def generate_models_or_sources_from_single_table(
    env: str, macro_name: str, macro_args: Dict[str, Any], profiles_path: pathlib.Path
) -> Dict[str, Any]:
    return yaml.safe_load(run_and_filter_dbt_macro(env, macro_name, macro_args, profiles_path))


def get_output_file_or_warn_if_exists(
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
