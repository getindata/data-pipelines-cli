# Changelog

## [Unreleased]

### Added
- Add documentation in the style of [Read the Docs](https://readthedocs.org/).
- Exception classes in `errors.py`, deriving from `DataPipelinesError` base exception class.
- Unit tests to massively improve code coverage.
- `--version` flag to **dp** command.

### Changed
- `dp compile`:
  - `--env` option has a default value: `local`,
  - `--datahub` is changed to `--datahub-gms-uri`, `--repository` is changed to `--docker-repository-uri`.
- `dp deploy`'s `--docker-push` is not a flag anymore and requires a Docker repository URI parameter; `--repository` got removed then.
- `dp run` and `dp test` run `dbt deps` before actual **dbt** command.
- Functions raise exceptions instead of exiting using `sys.exit(1)`; `cli.cli()` entrypoint is expecting exception and exits only there.
- `dp deploy` raises an exception if there is no Docker image to push or `build/config/dag` directory does not exist.

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

[Unreleased]: https://github.com/getindata/data-pipelines-cli/compare/0.6.0...HEAD

[0.6.0]: https://github.com/getindata/data-pipelines-cli/compare/0.5.1...0.6.0

[0.5.1]: https://github.com/getindata/data-pipelines-cli/compare/0.5.0...0.5.1

[0.5.0]: https://github.com/getindata/data-pipelines-cli/compare/0.4.0...0.5.0

[0.4.0]: https://github.com/getindata/data-pipelines-cli/compare/0.3.0...0.4.0

[0.3.0]: https://github.com/getindata/data-pipelines-cli/compare/0.2.0...0.3.0

[0.2.0]: https://github.com/getindata/data-pipelines-cli/compare/0.1.2...0.2.0

[0.1.2]: https://github.com/getindata/data-pipelines-cli/compare/0.1.1...0.1.2

[0.1.1]: https://github.com/getindata/data-pipelines-cli/compare/0.1.0...0.1.1

[0.1.0]: https://github.com/getindata/data-pipelines-cli/compare/5df87160e660d372a52a3665fe79be2029089613...0.1.0
