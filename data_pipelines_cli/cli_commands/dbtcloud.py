import json

import click
from typing import Any, Dict
from ..cli_constants import BUILD_DIR

from data_pipelines_cli.dbt_cloud_api_client import DbtCloudApiClient
from ..cli_utils import echo_info
from ..config_generation import read_dictionary_from_config_directory


def read_dbtcloud_config(env: str) -> Dict[str, Any]:
    """
    Read dbt Cloud configuration.

    :param env: Name of the environment
    :type env: str
    :return: Compiled dictionary
    :rtype: Dict[str, Any]
    """
    return read_dictionary_from_config_directory(BUILD_DIR.joinpath("dag"), env, "dbtcloud.yml")


@click.command(name="configure-cloud", help="Create dbt Cloud project")
@click.option(
    "--account_id",
    type=int,
    required=True,
    help="""dbt Cloud Account identifier To obtain your dbt Cloud account ID, sign into dbt Cloud in your browser.
     Take note of the number directly following the accounts path component of the URL - this is your account ID""",
)
@click.option(
    "--token",
    type=str,
    required=True,
    help="API token for your DBT Cloud account."
         "You can retrieve your User API token from your User Profile (top right icon) > API Access."
         "You can also use Service Token. Retrieve it from Account Settings > Service Tokens > Create Service Token.",
)
@click.option(
    "--remote_url",
    type=str,
    required=True,
    help="Git stores remote URL"
         " Note: After creating a dbt Cloud repository's SSH key, you will need to add the generated key text as"
         " a deploy key to the target repository. This gives dbt Cloud permissions to read / write in the repository."
)
@click.option(
    "--keyfile",
    type=str,
    required=True,
    help="Bigquery keyfile"
)
@click.option(
    "--env",
    default="local",
    type=str,
    help="Name of the environment",
    show_default=True)
def configure_cloud_command(
        account_id: int,
        token: str,
        remote_url: str,
        keyfile: str,
        env: str
) -> None:
    client = DbtCloudApiClient(f"https://cloud.getdbt.com/api", account_id, token)

    dbtcloud_config = read_dbtcloud_config(env)
    file = open(keyfile)
    keyfile_data = json.load(file)
    project_id = client.create_project(dbtcloud_config["project_name"])
    (repository_id, deploy_key) = client.create_repository(project_id, remote_url)
    echo_info("You need to add the generated key text as a deploy key to the target repository.\n"
              "This gives dbt Cloud permissions to read / write in the repository\n"
              f"{deploy_key}")

    for environment in dbtcloud_config["environments"]:
        if environment["type"] == "deployment":
            credentials_id = client.create_credentials(environment["dataset"], project_id)
        else:
            credentials_id = None
        environment_id = client.create_environment(project_id, environment["type"], environment["name"],
                                                   environment["dbt_version"], credentials_id)
        if environment["type"] == "deployment":
            client.create_job(project_id, environment_id, dbtcloud_config["schedule_interval"],
                              "Job - " + environment["name"])

    connection_id = client.create_bigquery_connection(
        project_id=project_id,
        name="BQ Connection Name",
        is_active=True,
        gcp_project_id=keyfile_data["project_id"],
        timeout_seconds=100,
        private_key_id=keyfile_data["private_key_id"],
        private_key=keyfile_data["private_key"],
        client_email=keyfile_data["client_email"],
        client_id=keyfile_data["client_id"],
        auth_uri=keyfile_data["auth_uri"],
        token_uri=keyfile_data["token_uri"],
        auth_provider_x509_cert_url=keyfile_data["auth_provider_x509_cert_url"],
        client_x509_cert_url=keyfile_data["client_x509_cert_url"]
    )

    client.associate_connection_repository(dbtcloud_config["project_name"], project_id, connection_id, repository_id)
