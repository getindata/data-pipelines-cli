import json
import requests


class DbtCloudApiClient:
    """A class used to create dbt Cloud project using API v3"""

    def __init__(self, host_url, account_id, token):
        self.host_url = host_url
        """Base URL differs for Multi and Single-Tenant Deployments"""

        self.account_id = account_id
        """
        To find your user ID in dbt Cloud, read the following steps:
        1. Go to Account Settings, Team, and then Users,
        2. Select your user,
        3. In the address bar, the number after /users is your user ID.
        """

        self.token = token
        """You can find your User API token in the Profile page under the API Access label"""

    def request(self, url, data):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Token {self.token}"
        }
        response = requests.post(
            url=url,
            data=data,
            headers=headers
        )
        res = json.loads(response.content)
        if not res["status"]["is_success"]:
            raise Exception(res["status"]["user_message"] + "\n" + res["data"])
        return res

    def create_project(self, name):
        """
        Note: the dbt_project_subdirectory is an optional field which allows you to point
        dbt Cloud to a subdirectory that lives within the root folder of your target repository.
        This means dbt Cloud will look for a dbt_project.yml file at that location.

        :param name: Name of the project
        :return: ID of created project
        """
        new_project = {
            "id": None,
            "account_id": self.account_id,
            "name": name,
            "dbt_project_subdirectory": None,
            "connection_id": None,
            "repository_id": None
        }

        new_project_data = json.dumps(new_project)

        response = self.request(f"{self.host_url}/v3/accounts/{str(self.account_id)}/projects/", new_project_data)
        return response["data"]["id"]

    def create_repository(self, project_id, git_clone_url):
        """
        Note: After creating  a dbt Cloud repository's SSH key, you will need to add the generated key text as
         a deploy key to the target repository. This gives dbt Cloud permissions to read / write in the repository.

        :param git_clone_url: Repository remote url
        :param project_id: ID of the project
        :return: repository ID and deploy key
        """
        new_repository = {
            "account_id": self.account_id,
            "project_id": project_id,
            "remote_url": git_clone_url,
            "git_clone_strategy": "deploy_key",
            "github_installation_id": None,
            "token_str": None
        }

        new_repository_data = json.dumps(new_repository)

        response = self.request(
            f"{self.host_url}/v3/accounts/{str(self.account_id)}/projects/{str(project_id)}/repositories/",
            new_repository_data)
        return response["data"]["id"], response["data"]["deploy_key"]["public_key"]

    def create_development_environment(self, project_id):
        """
        Create development environment

        :param project_id: ID of the project
        :return: ID of created environment
        """
        new_env = {
            "id": None,
            "type": "development",
            "name": "Development",
            "account_id": self.account_id,
            "project_id": project_id,
            "state": 1,
            "use_custom_branch": False,
            "custom_branch": None,
            "dbt_version": "1.0.0",
            "supports_docs": False,
        }

        new_env_data = json.dumps(new_env)

        response = self.request(
            f"{self.host_url}/v3/accounts/{str(self.account_id)}/projects/{str(project_id)}/environments/",
            new_env_data)
        return response["data"]["id"]

    def associate_connection_repository(self, name, project_id, connection_id=None, repository_id=None):
        """
        Link connection and repository to project

        :param name: Name of the project
        :param project_id: ID of the project
        :param connection_id: ID of the connection to be associated
        :param repository_id: ID of the repository to be associated
        :return: ID of the project
        """
        new_connection = {
            "name": name,
            "account_id": self.account_id,
            "id": project_id,
            "connection_id": connection_id,
            "repository_id": repository_id
        }

        new_connection_data = json.dumps(new_connection)
        response = self.request(f"{self.host_url}/v3/accounts/{str(self.account_id)}/projects/{str(project_id)}",
                                new_connection_data)

        return response["data"]["id"]

    def create_credentials(self, schema, project_id):
        """
        Create credentials

        :param schema: Default deployment dataset
        :param project_id: ID of the project
        :return: ID of created credentials
        """
        new_credentials = {
            "id": None,
            "account_id": self.account_id,
            "project_id": project_id,
            "type": "bigquery",
            "state": 1,
            "threads": 4,
            "schema": schema,
            "target_name": "default",
            "created_at": None,
            "updated_at": None,
            "username": None,
            "has_refresh_token": False
        }

        new_credentials_data = json.dumps(new_credentials)
        response = self.request(
            f"{self.host_url}/v3/accounts/{str(self.account_id)}/projects/{str(project_id)}/credentials/",
            new_credentials_data)

        return response["data"]["id"]

    def create_bigquery_connection(
            self,
            project_id,
            name,
            is_active,
            gcp_project_id,
            timeout_seconds,
            private_key_id,
            private_key,
            client_email,
            client_id,
            auth_uri,
            token_uri,
            auth_provider_x509_cert_url,
            client_x509_cert_url,
            retries=1,
            location=None,
            maximum_bytes_billed=0
    ):
        """
        Creates dbtCloud connection to BigQuery
        :param project_id: Name of the project
        :param name: Name of the connection
        :param is_active: should connection be active
        :return: ID of the created connection
        """
        connection_details = {
            "project_id": gcp_project_id,
            "timeout_seconds": timeout_seconds,
            "private_key_id": private_key_id,
            "private_key": private_key,
            "client_email": client_email,
            "client_id": client_id,
            "auth_uri": auth_uri,
            "token_uri": token_uri,
            "auth_provider_x509_cert_url": auth_provider_x509_cert_url,
            "client_x509_cert_url": client_x509_cert_url,
            "retries": retries,
            "location": location,
            "maximum_bytes_billed": maximum_bytes_billed
        }

        new_connection = {
            "id": None,
            "account_id": self.account_id,
            "project_id": project_id,
            "name": name,
            "type": "bigquery",
            "state": 1 if is_active else 0,
            "details": connection_details,
        }

        new_connection_data = json.dumps(new_connection).encode()
        response = self.request(f"{self.host_url}/v3/accounts/{self.account_id}/projects/{project_id}/connections/",
                                new_connection_data)

        return response["data"]["id"]
