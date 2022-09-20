import pathlib
import glob
import os
import yaml
import requests

from typing import Any, Dict, Tuple, Optional
from git import Repo
from shutil import rmtree, copytree, copy

from .config_generation import read_dictionary_from_config_directory
from .cli_constants import BUILD_DIR
from .cli_utils import echo_info, echo_subinfo, subprocess_run
from .config_generation import generate_profiles_yml
from .dbt_utils import run_dbt_command

LOOKML_DEST_PATH: pathlib.Path = BUILD_DIR.joinpath("lookml")

def read_looker_config(env: str) -> Dict[str, Any]:
    """Read Looker configuration file for project (``config/{env}/looker.yml``)
    :param env: Name of the environment
    :type env: str
    :return: Dictionary with their keys
    :rtype: LookerConfig
    """
    return read_dictionary_from_config_directory(
        BUILD_DIR.joinpath("dag"), env, "looker.yml"
    )

def generate_lookML_model(env: bool) -> None:
    looker_config = read_looker_config(env)
    subprocess_run([
        "dbt2looker",
        "--output-dir",
        LOOKML_DEST_PATH
        ])

def deploy_lookML_model(env: bool) -> None:
    looker_config = read_looker_config(env)
    local_repo_path = BUILD_DIR.joinpath("looker_project_repo")

    if local_repo_path.exists():
        echo_info(f"Removing {local_repo_path}")
        rmtree(local_repo_path)

    repo = Repo.clone_from(looker_config["looker_repository"], 
        local_repo_path)
    
    repo.git.checkout(looker_config["looker_repository_branch"])
    _copy_all_files_by_extention(LOOKML_DEST_PATH, local_repo_path.joinpath("models"), "model.lkml")
    _copy_all_files_by_extention(LOOKML_DEST_PATH, local_repo_path.joinpath("views"), "view.lkml")
    
    project_name, project_version = _get_project_name_and_version()
    _commit_and_push_changes(repo, project_name, project_version)
    _deploy_looker_project_to_production(looker_config["looker_instance_url"], looker_config["looker_project_id"], looker_config["looker_repository_branch"], looker_config["looker_webhook_secret"])

def _copy_all_files_by_extention(src: pathlib.Path, dest: pathlib.Path, files_extention: str) -> None:
    for file_path in glob.glob(os.path.join(src, '**', '*.' + files_extention), recursive=True):
        new_path = os.path.join(dest, os.path.basename(file_path))
        copy(file_path, new_path)

def _get_project_name_and_version() -> Tuple[str, str]:
    with open(pathlib.Path.cwd().joinpath("dbt_project.yml"), "r") as f:
        dbt_project_config = yaml.safe_load(f)
        return dbt_project_config["name"], dbt_project_config["version"]

def _commit_and_push_changes(repo: Repo, project_name: str, project_version: str) -> None:
        echo_info("Publishing")
        repo.git.add(all=True)
        repo.index.commit(f"Publication from project {project_name}, version: {project_version}")
        origin = repo.remote(name="origin")
        origin.push()

def _deploy_looker_project_to_production(looker_instance_url: str, project_id: str, branch: str, webhook_secret: str) -> None:
    headers = {"X-Looker-Deploy-Secret": webhook_secret}
    response = requests.post(
            url=f"{looker_instance_url}/webhooks/projects/{project_id}/deploy/branch/{branch}", 
            headers=headers
        )
