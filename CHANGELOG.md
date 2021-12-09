# Changelog

## [Unreleased]
### Added
- `dp run` and `dp test` commands.
- `dp clean` command for removing `build` and `target` directories.

### Modified
- `profiles.yml` gets generated and saved in `build` directory in `dp compile`, instead of relying on a local one in the
main project directory.
- `dp dbt <command>` generates `profiles.yml` in `build` directory by default.

### Removed
- Support for manually created `profiles.yml` in main project directory.

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

[Unreleased]: https://github.com/getindata/data-pipelines-cli/compare/0.3.0...HEAD

[0.3.0]: https://github.com/getindata/data-pipelines-cli/compare/0.2.0...0.3.0

[0.2.0]: https://github.com/getindata/data-pipelines-cli/compare/0.1.2...0.2.0

[0.1.2]: https://github.com/getindata/data-pipelines-cli/compare/0.1.1...0.1.2

[0.1.1]: https://github.com/getindata/data-pipelines-cli/compare/0.1.0...0.1.1

[0.1.0]: https://github.com/getindata/data-pipelines-cli/compare/5df87160e660d372a52a3665fe79be2029089613...0.1.0
