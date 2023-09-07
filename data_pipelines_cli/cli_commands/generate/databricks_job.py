import click
from dbt_databricks_factory.cli import create_job_cli
from dbt_databricks_factory.config import GitProvider


@click.command("databricks-job", help="Generate a Databricks job")
@click.argument(
    "manifest-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.option("--job-name", required=True, help="Name of the job to create.")
@click.option("--project-dir", required=True, help="Path to dbt project directory.")
@click.option("--profiles-dir", required=True, help="Path to dbt profiles directory.")
@click.option("--cron-schedule", help="Cron schedule for the job.")
@click.option(
    "--job-cluster", multiple=True, type=click.Tuple([str, str]), help="Job cluster config."
)
@click.option(
    "--task-cluster",
    multiple=True,
    type=click.Tuple([str, str]),
    help="Job cluster name or existing cluster id.",
)
@click.option("--default-task-cluster", help="Default task cluster name or existing cluster id.")
@click.option("--library", multiple=True, type=str, help="Libraries config.")
@click.option("--git-url", required=True, help="Git url.")
@click.option("--git-branch", help="Git branch.")
@click.option("--git-commit", help="Git commit.")
@click.option("--git-tag", help="Git tag.")
@click.option(
    "--git-provider",
    required=True,
    help="Git provider.",
    type=click.Choice([provider.value for provider in GitProvider]),
)
@click.option("--pretty", is_flag=True, help="Pretty print the output.")
@click.option(
    "--output-file",
    help="Output file path.",
    type=click.Path(file_okay=True, dir_okay=False, writable=True),
)
def generate_databricks_job_command(
    job_name: str,
    manifest_file: str,
    project_dir: str,
    profiles_dir: str,
    cron_schedule: str | None,
    job_cluster: list[tuple[str, str]],
    task_cluster: list[tuple[str, str]],
    default_task_cluster: str | None,
    library: list[str],
    git_url: str,
    git_branch: str | None,
    git_commit: str | None,
    git_tag: str | None,
    git_provider: str,
    pretty: bool,
    output_file: str,
) -> None:
    create_job_cli(
        job_name,
        manifest_file,
        project_dir,
        profiles_dir,
        cron_schedule,
        job_cluster,
        task_cluster,
        default_task_cluster,
        library,
        git_url,
        git_branch,
        git_commit,
        git_tag,
        git_provider,
        pretty,
        output_file,
    )
