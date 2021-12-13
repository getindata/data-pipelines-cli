import click
import yaml

from data_pipelines_cli.data_structures import read_config_or_exit


def list_templates() -> None:
    config = read_config_or_exit()

    click.echo("AVAILABLE TEMPLATES:\n")
    for tc in config["templates"].values():
        click.echo(yaml.dump(tc))


@click.command(name="template-list")
def list_templates_command() -> None:
    list_templates()
