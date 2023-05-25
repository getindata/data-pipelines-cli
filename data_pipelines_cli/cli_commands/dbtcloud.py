import json
from typing import Any, Dict

import click

from data_pipelines_cli.dbt_cloud_api_client import DbtCloudApiClient
from ..cli_constants import BUILD_DIR
from ..cli_utils import echo_info
from ..config_generation import read_dictionary_from_config_directory
from ..dbt_utils import _dump_dbt_vars_from_configs_to_string


def read_dbtcloud_config() -> Dict[str, Any]:
    """
    Read dbt Cloud configuration.

    :param env: Name of the environment
    :type env: str
    :return: Compiled dictionary
    :rtype: Dict[str, Any]
    """
    return read_dictionary_from_config_directory(BUILD_DIR.joinpath("dag"), ".", "dbtcloud.yml")


def read_bigquery_config(env: str) -> Dict[str, Any]:
    """
    Read dbt Cloud configuration.

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
    help="""dbt Cloud Account identifier To obtain your dbt Cloud account ID, sign into dbt Cloud
    in your browser. Take note of the number directly following the accounts path component of the
    URL - this is your account ID""",
)
@click.option(
    "--token",
    type=str,
    required=True,
    help="""API token for your DBT Cloud account. You can retrieve your User API token from your
    User Profile (top right icon) > API Access. You can also use Service Token. Retrieve it from
    Account Settings > Service Tokens > Create Service Token.""",
)
@click.option(
    "--remote_url",
    type=str,
    required=True,
    help="""Git stores remote URL Note: After creating a dbt Cloud repository's SSH key, you will
    need to add the generated key text as a deploy key to the target repository. This gives dbt
    Cloud permissions to read / write in the repository."""
)
@click.option(
    "--keyfile",
    type=str,
    required=True,
    help="Bigquery keyfile"
)
def configure_cloud_command(
        account_id: int,
        token: str,
        remote_url: str,
        keyfile: str) -> None:
    client = DbtCloudApiClient(f"https://cloud.getdbt.com/api", account_id, token)

    dbtcloud_config = read_dbtcloud_config()
    base_bq_config = read_bigquery_config("base")
    file = open(keyfile)
    keyfile_data = json.load(file)
    dbtcloud_project_id = client.create_project(dbtcloud_config["project_name"])
    (repository_id, deploy_key) = client.create_repository(dbtcloud_project_id, remote_url)
    echo_info("You need to add the generated key text as a deploy key to the target repository.\n"
              "This gives dbt Cloud permissions to read / write in the repository\n"
              f"{deploy_key}")

    environments_projects = {}
    for environment in dbtcloud_config["environments"]:
        bq_config = read_bigquery_config(environment["config_dir"])
        environments_projects[environment["name"]] = bq_config["project"]
        environment_id = create_environment(client, environment, bq_config["dataset"],
                                            dbtcloud_project_id)
        if environment["type"] == "deployment":
            dbt_vars = _dump_dbt_vars_from_configs_to_string(environment["config_dir"]).strip()
            client.create_job(dbtcloud_project_id, environment_id, environment["schedule_interval"],
                              "Job - " + environment["name"], dbt_vars)

    client.create_environment_variable(dbtcloud_project_id, base_bq_config["project"],
                                       environments_projects)

    connection_id = create_bq_connection(client, keyfile_data, dbtcloud_project_id)

    client.associate_connection_repository(dbtcloud_config["project_name"], dbtcloud_project_id,
                                           connection_id, repository_id)


def create_bq_connection(client, keyfile_data, project_id):
    """
    Creates a connection to the bigquery warehouse in the dbt Cloud project.

    :param client: API Client
    :param keyfile_data: Data read from Bigquery keyfile
    :param project_id: ID of the project in which the connection is to be created
    :return: ID of the created connection
    """
    return client.create_bigquery_connection(
        project_id=project_id,
        name="BQ Connection Name",
        is_active=True,
        gcp_project_id="{{ env_var(\"DBT_GCP_PROJECT\") }}",
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


def create_environment(client, environment, dataset, project_id):
    """
    Creates a dbt Cloud environment with the specified configuration

    :param client: API Client
    :param environment: Config of environment to be created
    :param project_id: ID of the project
    :param dataset: Name of target dataset
    :return: ID of created environment
    """
    if environment["type"] == "deployment":
        credentials_id = client.create_credentials(dataset, project_id)
    else:
        credentials_id = None
    environment_id = client.create_environment(project_id, environment["type"], environment["name"],
                                               environment["dbt_version"], credentials_id)
    return environment_id
