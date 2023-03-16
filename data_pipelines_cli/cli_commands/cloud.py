import json
from typing import Any, Dict, Optional

import click

from data_pipelines_cli.dbt_cloud_api_client import DbtCloudApiClient
from ..cli_constants import BUILD_DIR
from ..cli_utils import echo_info
from ..config_generation import read_dictionary_from_config_directory


def read_bigquery_config(env: str) -> Dict[str, Any]:
    """
    Read Bigquery configuration.

    :param env: Name of the environment
    :type env: str
    :return: Compiled dictionary
    :rtype: Dict[str, Any]
    """
    return read_dictionary_from_config_directory(BUILD_DIR.joinpath("dag"), env, "bigquery.yml")


@click.command(name="configure-cloud", help="Create dbt Cloud project")
@click.option(
    "--account_id",
    type=int,
    required=True,
    help="""dbt Cloud Account identifier To find your user ID in dbt Cloud, read the following steps:
        1. Go to Account Settings, Team, and then Users,
        2. Select your user,
        3. In the address bar, the number after /users is your user ID.""",
)
@click.option(
    "--token",
    type=str,
    required=True,
    help="API token for your DBT Cloud account.  "
         "You can find your User API token in the Profile page under the API Access label",
)
@click.option(
    "--remote_url",
    type=str,
    required=True,
    help="Note: After creating  a dbt Cloud repository's SSH key, you will need to add the generated key text as"
         " a deploy key to the target repository. This gives dbt Cloud permissions to read / write in the repository."
)
@click.option(
    "--project_name",
    type=str,
    required=False,
    default="Data Pipelines Project",
    help="Project Name",
)
@click.option("--keyfile", required=False, help="Bigquery keyfile")
@click.option("--env", default="local", type=str, help="Name of the environment", show_default=True)
def configure_cloud_command(
        account_id: int,
        token: str,
        remote_url: str,
        project_name: str,
        keyfile: Optional[str],
        env: str,
) -> None:
    client = DbtCloudApiClient(f"https://cloud.getdbt.com/api", account_id, token)

    bigquery_config = read_bigquery_config(env)

    if keyfile is None and not bigquery_config.get("method") == "service-account":
        echo_info("dbt Cloud requires service account")
        return

    file = open(keyfile or bigquery_config["keyfile"])
    keyfile_data = json.load(file)

    project_id = client.create_project(project_name)
    (repository_id, deploy_key) = client.create_repository(project_id, remote_url)
    echo_info("You need to add the generated key text as a deploy key to the target repository.\n"
              "This gives dbt Cloud permissions to read / write in the repository\n"
              f"{deploy_key}")

    credentials_id = client.create_credentials(bigquery_config["dataset"], project_id)
    client.create_development_environment(project_id, credentials_id)
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

    client.associate_connection_repository(project_name, project_id, connection_id, repository_id)
