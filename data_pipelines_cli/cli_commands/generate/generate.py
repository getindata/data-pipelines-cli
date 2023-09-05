import click

from .model_yaml import generate_model_yamls_command
from .source_sql import generate_source_sqls_command
from .source_yaml import generate_source_yamls_command
from dbt_databricks_factory.cli import create_job_cli

@click.group(name="generate", help="Generate additional dbt files")
def generate_group() -> None:
    pass


@click.command("databricks-job", help="Generate a Databricks job")
def generate_databricks_job_command() -> None:
    create_job_cli()

generate_group.add_command(generate_model_yamls_command)
generate_group.add_command(generate_source_sqls_command)
generate_group.add_command(generate_source_yamls_command)
