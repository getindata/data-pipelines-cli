# data-pipelines-cli

CLI for data platform

## Installation
TODO

## Usage
First, create a repository with a global configuration file that you or your organization will be using. The repository
should contain `dp.yml.tmpl` file looking similar to this:
```yaml
username: YOUR_USERNAME
templates:
  my-first-template:
    template_name: my-first-template
    template_path: https://github.com/<YOUR_USERNAME>/<YOUR_TEMPLATE>.git
source_type: bigquery
```
Thanks to the [copier](https://copier.readthedocs.io/en/stable/), you can leverage Jinja template syntax to create
easily modifiable configuration templates. Just create `copier.yml` file next to the `dp.yml.tmpl` one and configure
the template questions (read more at [copier documentation](https://copier.readthedocs.io/en/stable/configuring/)).

Then, run `dp init <CONFIG_REPOSITORY_URL>` to initialize **dp**. You can also drop `<CONFIG_REPOSITORY_URL>` argument,
**dp** will get initialized with default example config (although keep in mind it is very basic).

### Project creation

You can use `dp create <NEW_PROJECT_PATH>` to choose one of the templates added before and create the project in
`<NEW_PROJECT_PATH>` directory. You can also use `dp create <NEW_PROJECT_PATH> <LINK_TO_TEMPLATE_REPOSITORY>` to point
directly to a template repository. If `<LINK_TO_TEMPLATE_REPOSITORY>` proves to be a name of the template defined in
**dp**'s config file, `dp create` will choose the template by the name instead of trying to download the repository.

`dp template-list` lists all added templates.

### Project deployment

`dp deploy` will sync with your bucket provider. Provider will be chosen automatically based on the remote URL.
`dp deploy` also requires user to point to JSON or YAML file with provider-specific data like access tokens or project
names. E.g., to connect with Google Cloud Storage, one should run:
```bash
echo '{"token": "<PATH_TO_YOUR_TOKEN>", "project_name": "<YOUR_PROJECT_NAME>"}' > gs_args.json
dp deploy "gs://<YOUR_GS_PATH>" --blob-args gs_args.json
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.