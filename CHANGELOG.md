# Changelog

## [Unreleased]

### Added

-   `dp update` command
-   `dp publish` command for creation of dbt package out of the project.

### Changed

- Docker response in `deploy` and `compile` gets printed as processed strings instead of plain dictionaries.
- `dp compile` parses content of `datahub.yml` and replaces Jinja variables in the form of `var` or `env_var`.
- `dags_path` is read from an enved `airflow.yml` file.

## [0.10.0] - 2022-01-12

### Changed

-   Run `dbt deps` at the end of `dp prepare-env`.

### Fixed

-   `dp run` and `dp test` are no longer pointing to `profiles.yml` instead of the directory containing it.

## [0.9.0] - 2022-01-03

### Added

-   `--env` flag to `dp deploy`.

### Changed

-   Docker repository URI gets read out of `build/config/{env}/k8s.yml`.

### Removed

-   `--docker-repository-uri` and `--datahub-gms-uri` from `dp compile` and `dp deploy` commands.
-   `dp compile` no longer replaces `<INGEST_ENDPOINT>` in `datahub.yml`, or `<DOCKER_REPOSITORY_URL>` in `k8s.yml`

## [0.8.0] - 2021-12-31

### Changed

-   `dp init` and `dp create` automatically adds `.git` suffix to given template paths, if necessary.
-   When reading dbt variables, global-scoped variables take precedence over project-scoped ones (it was another way around before).
-   Address argument for `dp deploy` is no longer mandatory. It should be either placed in `airflow.yml` file as value of `dags_path` key, or provided with `--dags-path` flag.

## [0.7.0] - 2021-12-29

### Added

-   Add documentation in the style of [Read the Docs](https://readthedocs.org/).
-   Exception classes in `errors.py`, deriving from `DataPipelinesError` base exception class.
-   Unit tests to massively improve code coverage.
-   `--version` flag to **dp** command.
-   Add `dp prepare-env` command that prepares local environment for standalone **dbt** (right now, it only generates and saves `profiles.yml` in `$HOME/.dbt`).

### Changed

-   `dp compile`:
    -   `--env` option has a default value: `base`,
    -   `--datahub` is changed to `--datahub-gms-uri`, `--repository` is changed to `--docker-repository-uri`.
-   `dp deploy`'s `--docker-push` is not a flag anymore and requires a Docker repository URI parameter; `--repository` got removed then.
-   `dp run` and `dp test` run `dp compile` before actual **dbt** command.
-   Functions raise exceptions instead of exiting using `sys.exit(1)`; `cli.cli()` entrypoint is expecting exception and exits only there.
-   `dp deploy` raises an exception if there is no Docker image to push or `build/config/dag` directory does not exist.
-   Rename `gcp` to `gcs` in requirements (now one should run `pip install data-pipelines-cli[gcs]`).

## [0.6.0] - 2021-12-16

### Modified

-   **dp** saves generated `profiles.yml` in either `build/local` or `build/env_execution` directories. **dbt** gets executed with `env_execution` as the target.

## [0.5.1] - 2021-12-14

### Fixed

-   `_dbt_compile` is no longer removing replaced `<IMAGE_TAG>`.

## [0.5.0] - 2021-12-14

### Added

-   `echo_warning` function prints warning messages in yellow/orange color.

### Modified

-   Docker image gets built at the end of `compile` command.
-   **dbt**-related commands do not fail if no `$HOME/.dp.yml` exists (e.g., `dp run`).

### Removed

-   Dropped `dbt-airflow-manifest-parser` dependency.

## [0.4.0] - 2021-12-13

### Added

-   `dp run` and `dp test` commands.
-   `dp clean` command for removing `build` and `target` directories.
-   File synchronization tests for Google Cloud Storage using `gcp-storage-emulator`.
-   Read vars from config files (`$HOME/.dp.yml`, `config/$ENV/dbt.yml`) and pass to `dbt`.

### Modified

-   `profiles.yml` gets generated and saved in `build` directory in `dp compile`, instead of relying on a local one in the
    main project directory.
-   `dp dbt <command>` generates `profiles.yml` in `build` directory by default.
-   `dp init` is expecting `config_path` argument to download config template with the help of the `copier` and save it in `$HOME/.dp.yml`.
-   `dp template list` is renamed as `dp template-list`.
-   `dp create` allows for providing extra argument called `template-path`, being either name of one of templates defined
    in `.dp.yml` config file or direct link to Git repository.

### Removed

-   Support for manually created `profiles.yml` in main project directory.
-   `dp template new` command.
-   `username` field from `$HOME/.dp.yml` file.

## [0.3.0] - 2021-12-06

-   Run `dbt deps` alongside rest of `dbt` commands in `dp compile`

## [0.2.0] - 2021-12-03

-   Add support for GCP and S3 syncing in `dp deploy`

## [0.1.2] - 2021-12-02

-   Fix: do not use styled `click.secho` for Docker push response, as it may not be a `str`

## [0.1.1] - 2021-12-01

-   Fix Docker SDK for Python's bug related to tagging, which prevented Docker from pushing images.

## [0.1.0] - 2021-12-01

### Added

-   Draft of `dp init`, `dp create`, `dp template new`, `dp template list` and `dp dbt`
-   Draft of `dp compile` and `dp deploy`

[Unreleased]: https://github.com/getindata/data-pipelines-cli/compare/0.10.0...HEAD

[0.10.0]: https://github.com/getindata/data-pipelines-cli/compare/0.9.0...0.10.0

[0.9.0]: https://github.com/getindata/data-pipelines-cli/compare/0.8.0...0.9.0

[0.8.0]: https://github.com/getindata/data-pipelines-cli/compare/0.7.0...0.8.0

[0.7.0]: https://github.com/getindata/data-pipelines-cli/compare/0.6.0...0.7.0

[0.6.0]: https://github.com/getindata/data-pipelines-cli/compare/0.5.1...0.6.0

[0.5.1]: https://github.com/getindata/data-pipelines-cli/compare/0.5.0...0.5.1

[0.5.0]: https://github.com/getindata/data-pipelines-cli/compare/0.4.0...0.5.0

[0.4.0]: https://github.com/getindata/data-pipelines-cli/compare/0.3.0...0.4.0

[0.3.0]: https://github.com/getindata/data-pipelines-cli/compare/0.2.0...0.3.0

[0.2.0]: https://github.com/getindata/data-pipelines-cli/compare/0.1.2...0.2.0

[0.1.2]: https://github.com/getindata/data-pipelines-cli/compare/0.1.1...0.1.2

[0.1.1]: https://github.com/getindata/data-pipelines-cli/compare/0.1.0...0.1.1

[0.1.0]: https://github.com/getindata/data-pipelines-cli/compare/5df87160e660d372a52a3665fe79be2029089613...0.1.0
