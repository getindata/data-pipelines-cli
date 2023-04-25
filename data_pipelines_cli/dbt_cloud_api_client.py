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

        response = self.request(f"{self.host_url}/v3/accounts/{str(self.account_id)}/projects/",
                                new_project_data)
        return response["data"]["id"]

    def create_repository(self, project_id, git_clone_url):
        """
        Note: After creating  a dbt Cloud repository's SSH key, you will need to add the generated
        key text as a deploy key to the target repository. This gives dbt Cloud permissions to
        read / write in the repository.

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

    def create_environment(self, project_id, env_type, name, dbt_version, credentials_id=None):
        """
        Create environment. Environments encompass a collection of settings for how you want to run
        your dbt project. This includes: dbt version, git branch, data location (target schema).

        :param name: Name of the environment
        :param env_type: type of environment (development/deployment)
        :param project_id: ID of the project
        :param credentials_id: ID of credentials to be used by environment
        :param dbt_version: dbt version that should be used by this environment
        :return: ID of created environment
        """
        new_env = {
            "id": None,
            "type": env_type,
            "name": name,
            "account_id": self.account_id,
            "project_id": project_id,
            "state": 1,
            "use_custom_branch": False,
            "custom_branch": None,
            "dbt_version": dbt_version,
            "supports_docs": False,
            "credentials_id": credentials_id
        }

        new_env_data = json.dumps(new_env)

        response = self.request(
            f"{self.host_url}/v3/accounts/{str(self.account_id)}/projects/{str(project_id)}/environments/",
            new_env_data)
        return response["data"]["id"]

    def create_environment_variable(self, project_id, default, environments):
        """
        Create environment variable. Note: Environment variables must be prefixed with DBT_ or
        DBT_ENV_SECRET_ .

        :param project_id: ID of the project
        :param environments: dict which contains the value of the variable for each environment
        :param default: default environment variable value for project
        :return: IDs of created environment variable
        """
        env_var = {
            "new_name": "DBT_GCP_PROJECT",
            "project": default
        }
        env_var.update(environments)
        new_env = {
            "env_var": env_var
        }
        print(new_env)
        new_env_data = json.dumps(new_env)

        response = self.request(
            f"{self.host_url}/v3/accounts/{str(self.account_id)}/projects/{str(project_id)}/environment-variables/bulk/",
            new_env_data)
        return response["data"]["new_var_ids"]

    def associate_connection_repository(self, name, project_id, connection_id=None,
                                        repository_id=None):
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
        response = self.request(
            f"{self.host_url}/v3/accounts/{str(self.account_id)}/projects/{str(project_id)}",
            new_connection_data)

        return response["data"]["id"]

    def create_credentials(self, schema, project_id):
        """
        Creates credentials - these are needed to create the environment.

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
        response = self.request(
            f"{self.host_url}/v3/accounts/{self.account_id}/projects/{project_id}/connections/",
            new_connection_data)

        return response["data"]["id"]

    def create_job(self, project_id, environment_id, schedule_cron, name):
        """
        Creates sample job for given project and environment. Job is triggered by the scheduler
        executes commands: dbt seed, dbt test and dbt run.
        :param project_id: ID of the project
        :param environment_id: ID of the environment
        :param schedule_cron: Schedule (cron syntax)
        :param name: Name of the job
        :return: ID of created job
        """
        job_details = {
            "account_id": self.account_id,
            "project_id": project_id,
            "id": None,
            "environment_id": environment_id,
            "name": name,
            "dbt_version": None,
            "triggers": {
                "schedule": True,
                "github_webhook": False
            },
            "execute_steps": [
                "dbt seed",
                "dbt test",
                "dbt run"
            ],
            "settings": {
                "threads": 1,
                "target_name": "default"
            },
            "execution": {
                "timeout_seconds": 600
            },
            "state": 1,
            "schedule": {
                "cron": schedule_cron,
                "date": {
                    "type": "every_day"
                },
                "time": {
                    "type": "every_hour",
                    "interval": 1
                }
            }
        }

        job_details_data = json.dumps(job_details).encode()
        response = self.request(f"{self.host_url}/v2/accounts/{self.account_id}/jobs/",
                                job_details_data)

        return response["data"]["id"]
