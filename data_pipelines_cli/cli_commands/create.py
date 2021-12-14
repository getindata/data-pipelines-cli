import sys
from typing import Dict, Optional, Sequence

import click
import copier
import questionary

from data_pipelines_cli.cli_utils import echo_error, echo_warning
from data_pipelines_cli.data_structures import TemplateConfig, read_config_or_exit


def _choose_template(config_templates: Dict[str, TemplateConfig]) -> TemplateConfig:
    if len(config_templates) == 0:
        echo_error(
            "No template provided. Either run 'dp create <project_path> "
            "<link_to_template>' to use template from the link, or add template "
            "to `~/.dp.yml` file",
        )
        sys.exit(1)

    template_name = questionary.select("", choices=list(config_templates.keys())).ask()
    template_config = config_templates[template_name]

    return template_config


def _get_template_path(
    config_templates: Dict[str, TemplateConfig], template_path: Optional[str]
) -> str:
    if template_path:
        if template_path in config_templates.keys():
            to_return = config_templates[template_path]["template_path"]
        else:
            to_return = template_path
    else:
        to_return = _choose_template(config_templates)["template_path"]
    return to_return


def create(project_path: str, template_path: Optional[str]) -> None:
    config = read_config_or_exit()
    config_templates = config["templates"]
    src_template_path = _get_template_path(config_templates, template_path)
    copier.copy(src_path=src_template_path, dst_path=project_path)


@click.command(name="create")
@click.argument(
    "project-path",
    type=click.Path(writable=True, path_type=str, dir_okay=True, file_okay=False),
)
@click.argument("template-path", nargs=-1)
def create_command(project_path: str, template_path: Sequence[str]) -> None:
    if template_path and len(template_path) > 1:
        echo_warning(
            "dp create expects at most two arguments -- project-path and template-path"
        )
    create(project_path, template_path[0] if template_path else None)
