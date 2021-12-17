import shutil

import click

from ..cli_constants import BUILD_DIR
from ..cli_utils import echo_info, echo_subinfo, subprocess_run


def _dbt_clean() -> None:
    echo_info("dbt clean")
    subprocess_run(["dbt", "clean"])


def _remove_build_dir() -> None:
    if BUILD_DIR.exists():
        echo_info(f"Removing {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR)
        echo_subinfo(f"{BUILD_DIR} removed")


def clean() -> None:
    """Deletes local working directories"""
    _dbt_clean()
    _remove_build_dir()


@click.command(name="clean", help="Delete local working directories")
def clean_command() -> None:
    clean()
