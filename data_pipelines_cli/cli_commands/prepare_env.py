import os
import pathlib
from typing import Any, Dict

import click
import yaml
from jinja2 import BaseLoader, DictLoader
from jinja2.nativetypes import NativeEnvironment

from data_pipelines_cli.cli_utils import echo_subinfo
from data_pipelines_cli.config_generation import DbtProfile, generate_profiles_dict
from data_pipelines_cli.dbt_utils import read_dbt_vars_from_configs
from data_pipelines_cli.errors import JinjaVarKeyError


def _prepare_jinja_replace_environment(
    jinja_loader: BaseLoader, dbt_vars: Dict[str, Any]
) -> NativeEnvironment:
    def _jinja_vars(var_name: str) -> Any:
        return dbt_vars[var_name]

    def _jinja_env_vars(var_name: str) -> Any:
        return os.environ[var_name]

    jinja_env = NativeEnvironment(loader=jinja_loader)
    # Hacking Jinja to use our functions, following:
    # https://stackoverflow.com/a/6038550
    jinja_env.globals["var"] = _jinja_vars
    jinja_env.globals["env_var"] = _jinja_env_vars

    return jinja_env


def _replace_outputs_vars_with_values(
    outputs_setting_dict: Dict[str, Any], dbt_vars: Dict[str, Any]
) -> Dict[str, Any]:
    jinja_loader = DictLoader(outputs_setting_dict)
    jinja_env = _prepare_jinja_replace_environment(jinja_loader, dbt_vars)

    rendered_settings = {}
    for setting_key, setting_old_value in outputs_setting_dict.items():
        try:
            rendered_settings[setting_key] = jinja_env.get_template(
                setting_key
            ).render()
        except TypeError:
            # Jinja is accepting only str or Template and fails on int, etc.
            rendered_settings[setting_key] = setting_old_value
        except KeyError as key_error:
            # Variable does not exist and _jinja_vars or _jinja_env_vars thrown
            raise JinjaVarKeyError(key_error.args[0])
    return rendered_settings


def _replace_profiles_vars_with_values(
    profile: Dict[str, DbtProfile], dbt_vars: Dict[str, Any]
) -> Dict[str, DbtProfile]:
    for targets_dict in profile.values():
        new_outputs = {}
        for target, settings_dict in targets_dict["outputs"].items():
            new_outputs[target] = _replace_outputs_vars_with_values(
                settings_dict, dbt_vars
            )
        targets_dict["outputs"] = new_outputs

    return profile


def prepare_env(env: str) -> None:
    """
    Prepares local environment for use with applications expecting a "traditional"
    dbt structure, such as plugins to VS Code. If in doubt, use ``dp run`` and
    ``dp test`` instead.

    :param env: Name of the environment
    :type env: str
    """
    profile = _replace_profiles_vars_with_values(
        generate_profiles_dict(env, True), read_dbt_vars_from_configs(env)
    )

    home_profiles_path = pathlib.Path.home().joinpath(".dbt", "profiles.yml")
    home_profiles_path.parent.mkdir(parents=True, exist_ok=True)
    with open(home_profiles_path, "w") as profiles:
        yaml.dump(profile, profiles, default_flow_style=False)

    echo_subinfo(f"Saved profiles.yml in {home_profiles_path}")


@click.command(
    name="prepare-env",
    help="Prepare local environment for apps interfacing with dbt",
)
@click.option("--env", default="local", type=str, help="Name of the environment")
def prepare_env_command(env: str) -> None:
    prepare_env(env)
