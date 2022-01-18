import pathlib
from typing import Dict

import click
import yaml

from ..cli_utils import echo_subinfo
from ..config_generation import DbtProfile, generate_profiles_dict
from ..dbt_utils import read_dbt_vars_from_configs, run_dbt_command
from ..jinja import replace_vars_with_values


def prepare_env(env: str) -> None:
    """
    Prepare local environment for use with dbt-related applications.

    Prepare local environment for use with applications expecting a "traditional"
    dbt structure, such as plugins to VS Code. If in doubt, use ``dp run`` and
    ``dp test`` instead.

    :param env: Name of the environment
    :type env: str
    """
    profile: Dict[str, DbtProfile] = replace_vars_with_values(
        generate_profiles_dict(env, True), read_dbt_vars_from_configs(env)
    )

    home_profiles_path = pathlib.Path.home().joinpath(".dbt", "profiles.yml")
    home_profiles_path.parent.mkdir(parents=True, exist_ok=True)
    with open(home_profiles_path, "w") as profiles:
        yaml.dump(profile, profiles, default_flow_style=False)

    echo_subinfo(f"Saved profiles.yml in {home_profiles_path.parent}")
    run_dbt_command(("deps",), env, home_profiles_path.parent)


@click.command(
    name="prepare-env",
    help="Prepare local environment for apps interfacing with dbt",
)
@click.option("--env", default="local", type=str, help="Name of the environment")
def prepare_env_command(env: str) -> None:
    prepare_env(env)
