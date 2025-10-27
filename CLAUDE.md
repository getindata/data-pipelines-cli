# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**data-pipelines-cli** (`dp`) is a CLI tool for managing data platform workflows. It orchestrates dbt projects, cloud deployments, Docker builds, and multi-service integrations (Airbyte, DataHub, Looker). Projects are created from templates using copier, compiled with environment-specific configs, and deployed to cloud storage (GCS, S3).

**Version:** 0.30.0 | **Python:** 3.9+ | **License:** Apache 2.0

## Quick Command Reference

### Development
```bash
# Setup
pip install -e .[tests,bigquery,docker,datahub,gcs,s3]
pip install -r requirements-dev.txt && pre-commit install

# Testing
pytest --cov data_pipelines_cli --cov-report term-missing --ignore=venv
pytest tests/test_dbt_utils.py::test_specific_function
tox -e py39

# Linting
pre-commit run --all-files
black data_pipelines_cli tests
flake8 data_pipelines_cli tests
mypy data_pipelines_cli
```

### CLI Workflow
```bash
# Initialize global config
dp init https://github.com/org/dp-config.git

# Create project from template
dp create ./my_pipeline my-template-name --vcs-ref develop

# Local development
dp prepare-env --env local       # Setup IDE integration
dp compile --env local           # Compile dbt project
dp run --env local               # Run dbt models
dp test --env local              # Run dbt tests
dp seed --env local              # Load seed data
dp docs-serve --env local        # Serve docs on port 8080

# Code generation
dp generate source-yaml --env local --source-path models/sources schema1 schema2
dp generate model-yaml --env local --model-paths models/marts --overwrite
dp generate databricks-job --env prod --python-code-path jobs/script.py

# Production deployment
dp compile --env prod --docker-build --docker-tag v1.0.0
dp deploy --env prod \
  --docker-push \
  --datahub-ingest \
  --bi-git-key-path ~/.ssh/looker_key \
  --dags-path gs://airflow-bucket/dags \
  --blob-args gcs_creds.json

# Cleanup
dp clean
```

## Architecture

### Directory Structure
```
data_pipelines_cli/
├── cli.py                    # Entry point, command registration, global error handler
├── cli_commands/             # Command implementations
│   ├── init.py              # Initialize ~/.dp.yml config
│   ├── create.py            # Create project from template (copier)
│   ├── update.py            # Update existing project
│   ├── compile.py           # Compile: copy files, merge configs, dbt compile, docker build
│   ├── run.py               # Execute dbt models
│   ├── test.py              # Run dbt tests
│   ├── seed.py              # Load dbt seed data
│   ├── docs.py              # Serve dbt documentation
│   ├── deploy.py            # Deploy: docker push, datahub, airbyte, looker, cloud sync
│   ├── publish.py           # Publish dbt package to Git
│   ├── prepare_env.py       # Generate ~/.dbt/profiles.yml for local dev
│   ├── clean.py             # Remove build/ directory
│   ├── template.py          # List available templates
│   └── generate/            # Code generation subcommands
│       ├── generate.py      # Command group entry point
│       ├── source_yaml.py   # Generate dbt source schemas from DB
│       ├── model_yaml.py    # Generate dbt model schemas
│       ├── source_sql.py    # Generate dbt source SQL
│       └── databricks_job.py # Generate Databricks job configs
├── config_generation.py      # Config merging, profiles.yml generation
├── dbt_utils.py             # dbt command execution with variable management
├── filesystem_utils.py      # Cloud storage sync (LocalRemoteSync class)
├── jinja.py                 # Jinja2 variable substitution in configs
├── airbyte_utils.py         # Airbyte API client (AirbyteFactory)
├── bi_utils.py              # BI platform orchestration
├── looker_utils.py          # LookML generation and Git deployment
├── docker_response_reader.py # Docker API response parser
├── cli_utils.py             # Echo functions, subprocess wrapper
├── cli_constants.py         # BUILD_DIR, ENV_CONFIGURATION_PATH, defaults
├── data_structures.py       # TypedDict PODs (DataPipelinesConfig, DbtModel, etc.)
├── errors.py                # Custom exception hierarchy
├── io_utils.py              # File operations, git hash detection
└── vcs_utils.py             # Git URL normalization
```

### Configuration System

**Layered merging** with precedence (highest to lowest):
```
CLI arguments
  ↓
config/{env}/*.yml (environment-specific)
  ↓
config/base/*.yml (defaults)
  ↓
~/.dp.yml (global vars and templates)
```

**Implementation:** `config_generation.read_dictionary_from_config_directory(path, env, file)` merges base + env configs using `dict(base, **env)`.

**Variable resolution** for dbt:
```python
# dbt_utils.read_dbt_vars_from_configs(env) merges:
{
  **config/base/dbt.yml['vars'],
  **config/{env}/dbt.yml['vars'],
  **~/.dp.yml['vars']
}
```

### Key Workflows

#### Compile Flow
```
dp compile --env prod --docker-build
  ├─ Copy dag/ → build/dag/
  ├─ Copy config/ → build/dag/config/
  ├─ Merge configs: base + prod
  ├─ Replace Jinja vars in datahub.yml
  ├─ Generate profiles.yml from dbt.yml + bigquery.yml
  ├─ Run: dbt deps → dbt compile → dbt docs generate → dbt source freshness
  ├─ Copy target/manifest.json → build/dag/manifest.json
  ├─ docker build -t repo:tag [if --docker-build]
  └─ Generate Looker LookML [if bi.yml configured]
```

#### Deploy Flow
```
dp deploy --env prod --docker-push --datahub-ingest
  ├─ docker push repo:tag
  ├─ datahub ingest -c config/prod/datahub.yml
  ├─ Airbyte: create/update connections via REST API
  ├─ Looker: clone repo → generate LookML → commit/push
  └─ Cloud sync: LocalRemoteSync(build/dag, gs://bucket)
     ├─ List local files
     ├─ Push each to GCS/S3 via fsspec
     └─ Delete remote files not in local
```

#### dbt Execution
```python
# All dbt commands use:
run_dbt_command(("run",), env, profiles_path)
  → dbt run --profile bigquery --profiles-dir build/profiles/prod
            --target env_execution --vars '{var1: val1, ...}'
```

### Important Files

| File | Lines | Purpose |
|------|-------|---------|
| **cli_commands/compile.py** | 160+ | Orchestrates compilation: file copying, config merging, dbt compile, Docker build |
| **cli_commands/deploy.py** | 240+ | Orchestrates deployment: Docker, DataHub, Airbyte, Looker, cloud storage |
| **config_generation.py** | 175+ | Config merging logic, profiles.yml generation |
| **dbt_utils.py** | 95+ | dbt subprocess execution with variable aggregation |
| **filesystem_utils.py** | 75+ | LocalRemoteSync class for cloud storage (uses fsspec) |
| **data_structures.py** | 153+ | TypedDict definitions for all config PODs |
| **airbyte_utils.py** | 150+ | AirbyteFactory for connection management via REST API |
| **looker_utils.py** | 100+ | LookML generation (dbt2looker) and Git deployment |
| **jinja.py** | 60+ | replace_vars_with_values() for config template rendering |

## Dependencies

### Core (always installed)
- **click** (8.1.3): CLI framework
- **copier** (7.0.1): Project templating
- **dbt-core** (1.7.3): Data build tool
- **fsspec** (2023.12.1): Cloud filesystem abstraction
- **jinja2** (3.1.2): Template rendering
- **pyyaml** (6.0.1): Config parsing
- **pydantic** (<2): Validation

### Optional Extras
```bash
# dbt adapters
pip install data-pipelines-cli[bigquery]     # dbt-bigquery==1.7.2
pip install data-pipelines-cli[snowflake]    # dbt-snowflake==1.7.1
pip install data-pipelines-cli[postgres]     # dbt-postgres==1.7.3
pip install data-pipelines-cli[databricks]   # dbt-databricks-factory
pip install data-pipelines-cli[dbt-all]      # All adapters

# Cloud/integrations
pip install data-pipelines-cli[docker]       # docker==6.0.1
pip install data-pipelines-cli[datahub]      # acryl-datahub[dbt]
pip install data-pipelines-cli[looker]       # dbt2looker==0.11.0
pip install data-pipelines-cli[gcs]          # gcsfs==2023.12.1
pip install data-pipelines-cli[s3]           # s3fs==2023.12.1

# Development
pip install data-pipelines-cli[tests]        # pytest, moto, coverage
pip install data-pipelines-cli[docs]         # sphinx, sphinx-click
```

## Development Patterns

### Error Handling
```python
# All exceptions inherit from DataPipelinesError
# Global handler in cli.py catches and formats errors
try:
    command_logic()
except DataPipelinesError as err:
    echo_error(f"CLI Error: {err.message}")
    if err.submessage:
        echo_suberror(err.submessage)
    sys.exit(1)
```

### Optional Dependencies
```python
# Check at function start, raise clear error
try:
    import docker
except ModuleNotFoundError:
    raise DockerNotInstalledError()
# Error message tells user: "pip install data-pipelines-cli[docker]"
```

### Subprocess Execution
```python
# All subprocess calls use wrapper:
subprocess_run(["dbt", "run"], capture_output=False)
# Automatically raises SubprocessNonZeroExitError on failure
```

### Config Reading
```python
# Standard pattern for all config reads:
config = read_dictionary_from_config_directory(
    BUILD_DIR.joinpath("dag"),
    env,
    "filename.yml"
)
# Returns merged dict: {...base, **env}
```

## Important Constants

```python
BUILD_DIR = pathlib.Path.cwd().joinpath("build")
ENV_CONFIGURATION_PATH = pathlib.Path.home().joinpath(".dp.yml")
PROFILE_NAME_LOCAL_ENVIRONMENT = "local"
PROFILE_NAME_ENV_EXECUTION = "env_execution"
IMAGE_TAG_TO_REPLACE = "<IMAGE_TAG>"
```

## PR Workflow

1. Fork from `develop` branch
2. Install dev dependencies and pre-commit hooks
3. Write unit tests (tests mirror source structure)
4. Update CHANGELOG.md (keep-a-changelog format)
5. Ensure pre-commit passes (isort, black, flake8, mypy)
6. Squash commits with verbose PR name
7. Open PR against `develop`

**Code Quality:**
- Max line length: 100 chars
- Type hints required (mypy checked)
- Test naming: `test_*` prefix
- Mock external services: moto (S3), gcp-storage-emulator (GCS)

## Release Process

1. Run [Prepare Release](https://github.com/getindata/data-pipelines-cli/actions?query=workflow%3A%22Prepare+release%22) action
2. Review auto-generated PR for version bump and changelog
3. Merge PR to `main`
4. [Publish](https://github.com/getindata/data-pipelines-cli/actions?query=workflow%3APublish) workflow auto-publishes to PyPI and merges back to `develop`

## Project Structure (User Projects)

```
my_pipeline/                  # Created by dp create
├── .copier-answers.yml      # Template metadata
├── dbt_project.yml          # dbt configuration
├── config/
│   ├── base/
│   │   ├── dbt.yml         # target_type, vars
│   │   ├── bigquery.yml    # Warehouse credentials/settings
│   │   ├── airflow.yml     # dags_path for deployment
│   │   ├── datahub.yml     # Metadata ingestion config
│   │   ├── airbyte.yml     # Connection definitions
│   │   └── bi.yml          # Looker/BI settings
│   └── {env}/              # Environment overrides (prod, dev, staging)
│       └── *.yml           # Same files as base/, merged on top
├── dag/                     # Airflow/orchestration code
├── models/
│   ├── sources/
│   ├── staging/
│   └── marts/
└── build/                   # Generated by dp compile (git ignored)
    ├── dag/                 # Copy of dag/ with configs
    └── profiles/            # Generated dbt profiles.yml
```

## Tips

- **BUILD_DIR** is the working directory for all compilation/execution
- **Always run `dp clean`** between environment switches to avoid stale artifacts
- **Environment names** map to dbt targets: `local` → `local`, everything else → `env_execution`
- **Jinja variables** in configs support `{{ var('key') }}` and `{{ env_var('KEY') }}`
- **Cloud storage sync** uses fsspec, so any fsspec backend works (gs://, s3://, az://, etc.)
- **Code generation** requires compilation first (needs manifest.json)
- **Test mocking:** S3 uses moto, GCS uses gcp-storage-emulator
