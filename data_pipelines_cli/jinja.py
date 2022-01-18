import os
from typing import Any, Dict

from jinja2 import BaseLoader, DictLoader
from jinja2.nativetypes import NativeEnvironment

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


def replace_vars_with_values(
    templated_dictionary: Dict[str, Any], dbt_vars: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Replace variables in given dictionary using Jinja template in its values.

    :param templated_dictionary: Dictionary with Jinja-templated values
    :type templated_dictionary: Dict[str, Any]
    :param dbt_vars: Variables to replace
    :type dbt_vars: Dict[str, Any]
    :return: Dictionary with replaced variables
    :rtype: Dict[str, Any]
    :raises JinjaVarKeyError: Variable referenced in Jinja template does not exist
    """
    jinja_loader = DictLoader(templated_dictionary)
    jinja_env = _prepare_jinja_replace_environment(jinja_loader, dbt_vars)

    rendered_settings = {}
    for setting_key, setting_old_value in templated_dictionary.items():
        if isinstance(setting_old_value, dict):
            rendered_settings[setting_key] = replace_vars_with_values(
                setting_old_value, dbt_vars
            )
        else:
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
