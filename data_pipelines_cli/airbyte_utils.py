#%%
#TODO 
# Check if exist
# Create
# Update

import yaml
import requests
import pathlib
from cli_constants import BUILD_DIR
from cli_utils import echo_warning
# find_datahub_config_file
import os
import json
import ast

def find_config_file(env: str, config_name: str) -> pathlib.Path:
    if BUILD_DIR.joinpath("dag", "config", env, f"{config_name}.yml").is_file():
        return BUILD_DIR.joinpath("dag", "config", env, f"{config_name}.yml")
    return BUILD_DIR.joinpath("dag", "config", "base", f"{config_name}.yml")


def factory(env: str, config_name: str) -> None:
    airbyte_config_path = find_config_file(env, config_name)
    with open(airbyte_config_path, "r") as airbyte_config_file:
        airbyte_config = yaml.safe_load(airbyte_config_file)
    airbyte_url = airbyte_config['airbyte_url']
    if airbyte_config["connections"]:
        [create_update_connection(airbyte_config["connections"][connection], airbyte_url) for connection in airbyte_config["connections"]]
        [task.update(env_replacer(task)) for task in airbyte_config['tasks']]
        update_file(airbyte_config, airbyte_config_path)


def update_file(updated_config: dict, airbyte_config_path: pathlib.Path) -> None:
    with open(airbyte_config_path, "w") as airbyte_config_file:
        yaml.safe_dump(updated_config, airbyte_config_file)


def env_replacer(config: dict) -> dict:
    return ast.literal_eval(os.path.expandvars(f"{config}"))

def request_handler(airbyte_api_url: str, config: dict) -> dict: 
    headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url = airbyte_api_url, headers=headers, data=json.dumps(config))
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as e:
        print(e.response.text)

def create_update_connection(connection_config: dict, airbyte_url: str) -> None:
    response_search = request_handler(f"{airbyte_url}/api/v1/connections/search", {"sourceId": connection_config['sourceId'], "destinationId": connection_config['destinationId']})
    print(response_search)
    if not response_search['connections']:
        response_create = request_handler(f"{airbyte_url}/api/v1/connections/create", connection_config)
        os.environ[response_create['name']] = response_create['connectionId']
    else:
        connection_config.pop("sourceId", None)
        connection_config.pop("destinationId", None)
        connection_config['connectionId'] = response_search["connections"][0]['connectionId']
        request_handler(f"{airbyte_url}/api/v1/connections/update", connection_config)


#%% 
factory("prod", "airbyte")
# %%
