## PR Guidelines
1. Fork branch from `develop`.
2. Ensure to provide unit tests for new functionality.
3. Install dev requirements: `pip install -r requirements-dev.txt` and setup a hook: `pre-commit install`.
4. Update documentation accordingly.
5. Update [changelog](CHANGELOG.md) according to ["Keep a changelog"](https://keepachangelog.com/en/1.0.0/) guidelines.
6. Squash changes with a single commit as much as possible and ensure verbose PR name.
7. Open a PR against the `develop` branch.

*We reserve the right to take over and modify or abandon PRs that do not match the workflow or are abandoned.*

## Release workflow

1. Create the release candidate:
    - Go to the [Prepare release](https://github.com/getindata/data-pipelines-cli/actions?query=workflow%3A%22Prepare+release%22) action.
    - Click "Run workflow"
    - Enter the part of the version to bump (one of `<major>.<minor>.<patch>`). Minor (x.**x**.x) is a default.
2. If the workflow has run sucessfully:
    - Go to the newly openened PR named `Release candidate <version>`
    - Check that changelog and version have been properly updated. If not pull the branch and apply manual changes if necessary.
    - Merge the PR to main
3. Checkout the [Publish](https://github.com/getindata/data-pipelines-cli/actions?query=workflow%3APublish) workflow to see if:
    - The package has been uploaded on PyPI successfully
    - The changes have been merged back to develop
