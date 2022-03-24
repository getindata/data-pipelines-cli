import click

from .model_yaml import generate_model_yamls_command
from .source_sql import generate_source_sqls_command
from .source_yaml import generate_source_yamls_command


@click.group(name="generate", help="Generate additional dbt files")
def generate_group() -> None:
    pass


generate_group.add_command(generate_model_yamls_command)
generate_group.add_command(generate_source_sqls_command)
generate_group.add_command(generate_source_yamls_command)
