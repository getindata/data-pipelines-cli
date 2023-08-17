# About

This document instructs how to generate `tests/goldens/manifest.json` for a particular dbt and manifest schema version.

# Tutorial

dbt version to manifest version mapping is documented here: https://docs.getdbt.com/reference/artifacts/manifest-json


## dbt Core v.5.4 (Manifest version v9)

### 1. Prepare environment

```
virtualenv manifest_test --python=python3.9
source manifest_test/bin/activate
(manifest_test) % pip install -r requirements.txt
```
Where `requirements.txt` contains the following packages (please check which plugin version is compatible with a corresponding dbt version).

```
acryl-datahub[dbt]==0.10.4
dbt-core==1.5.4
dbt-spark==1.5.2
dbt-bigquery==1.5.5
dbt-postgres==1.5.4
dbt-snowflake==1.5.2
dbt-redshift==1.5.9
```

### 2. Init dbt

```commandline
(manifest_test) % mkdir manifest_test_project
(manifest_test) % cd manifest_test_project
(manifest_test) % dbt init
```
Fill in the information in the wizard as below.

```
Running with dbt=1.5.4
Enter a name for your project (letters, digits, underscore): my_new_project
Which database would you like to use?
[1] bigquery
[2] snowflake
[3] redshift
[4] postgres
[5] spark
Enter a number: 1
[1] oauth
[2] service_account
Desired authentication method option (enter a number): 1
project (GCP project id): exampleproject
dataset (the name of your dbt dataset): username_private_working_dataset
threads (1 or more): 1
job_execution_timeout_seconds [300]: 150
[1] US
[2] EU
Desired location option (enter a number): 1
15:07:20  Profile my_new_project written to /Users/your-user/.dbt/profiles.yml using target's profile_template.yml and your supplied values. Run 'dbt debug' to validate the connection.
15:07:20
Your new dbt project "my_new_project" was created!
```

### 3. Compile your dbt project

Navigate to your newly created project and run `dbt compile`:

```
cd my_new_project
dbt compile
```

You can find the generated `manifest.json` file in `target` folder.

### 4. Copy manifest to your data-pipelines-cli branch

Overwrite `tests/goldens/manifest.json` on your local branch of `data-pipelines-cli` repository with the generated `manifest.json`. Verify if tests run successfully, if not - adjust the code to the new version of Manifest.

Navigate to folder my_new_project2p/target where manifest.json has just been generated