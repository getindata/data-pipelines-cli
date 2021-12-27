import click
import yaml

from data_pipelines_cli.data_structures import read_config


def list_templates() -> None:
    """Print a list of all templates saved in the config file"""
    config = read_config()

    click.echo("AVAILABLE TEMPLATES:\n")
    for tc in config["templates"].values():
        click.echo(yaml.dump(tc))


@click.command(
    name="template-list", help="Print a list of all templates saved in the config file"
)
def list_templates_command() -> None:
    list_templates()
