import click
import copier
from copier.config.objects import NoSrcPathError

from data_pipelines_cli.cli_utils import echo_warning
from data_pipelines_cli.errors import NotAProjectDirectoryError


def update(project_path: str, vcs_ref: str) -> None:
    """
    Update an existing project from its template
    :param project_path: Path to a directory to create
    :type project_path: str
    :param vcs_ref: Git reference to checkout in projects template
    :type vcs_ref: str
    """
    try:
        copier.copy(dst_path=project_path, vcs_ref=vcs_ref, force=True)
    except NoSrcPathError:
        raise NotAProjectDirectoryError(project_path)


@click.command(name="update", help="Update project from its template")
@click.argument("project-path", nargs=-1)
@click.option("--vcs-ref", default="HEAD", type=str, help="Git reference to checkout")
def update_command(project_path: str, vcs_ref: str) -> None:
    if len(project_path) > 1:
        echo_warning("dp expects at most 1 argument -- project-path")
    update(project_path[0] if project_path else ".", vcs_ref)
