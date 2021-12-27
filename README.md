# data-pipelines-cli

CLI for data platform

## Installation
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install [dp (data-pipelines-cli)](https://pypi.org/project/data-pipelines-cli/):

```bash
pip install data-pipelines-cli[docker,datahub,gcs]
```

## Usage
First, create a repository with a global configuration file that you or your organization will be using. The repository
should contain `dp.yml.tmpl` file looking similar to this:
```yaml
templates:
  my-first-template:
    template_name: my-first-template
    template_path: https://github.com/<YOUR_USERNAME>/<YOUR_TEMPLATE>.git
vars:
  username: YOUR_USERNAME
```
Thanks to the [copier](https://copier.readthedocs.io/en/stable/), you can leverage Jinja template syntax to create
easily modifiable configuration templates. Just create a `copier.yml` file next to the `dp.yml.tmpl` one and configure
the template questions (read more at [copier documentation](https://copier.readthedocs.io/en/stable/configuring/)).

Then, run `dp init <CONFIG_REPOSITORY_URL>` to initialize **dp**. You can also drop `<CONFIG_REPOSITORY_URL>` argument,
**dp** will get initialized with an empty config.

### Project creation

You can use `dp create <NEW_PROJECT_PATH>` to choose one of the templates added before and create the project in the
`<NEW_PROJECT_PATH>` directory. You can also use `dp create <NEW_PROJECT_PATH> <LINK_TO_TEMPLATE_REPOSITORY>` to point
directly to a template repository. If `<LINK_TO_TEMPLATE_REPOSITORY>` proves to be the name of the template defined in
**dp**'s config file, `dp create` will choose the template by the name instead of trying to download the repository.

`dp template-list` lists all added templates.

### Project deployment

`dp deploy` will sync with your bucket provider. The provider will be chosen automatically based on the remote URL.
`dp deploy` also requires the user to point to JSON or YAML file with provider-specific data like access tokens or project
names. E.g., to connect with Google Cloud Storage, one should run:
```bash
echo '{"token": "<PATH_TO_YOUR_TOKEN>", "project_name": "<YOUR_PROJECT_NAME>"}' > gs_args.json
dp deploy "gs://<YOUR_GS_PATH>" --blob-args gs_args.json
```

When finished, call `dp clean` to remove compilation related directories.

### Variables
You can put a dictionary of variables to be passed to `dbt` in your `config/<ENV>/dbt.yml` file, following the convention
presented in [the guide at the dbt site](https://docs.getdbt.com/docs/building-a-dbt-project/building-models/using-variables#defining-variables-in-dbt_projectyml).
E.g., if one of the fields of `config/<SNOWFLAKE_ENV>/snowflake.yml` looks like this:
```yaml
schema: "{{ var('snowflake_schema') }}"
```
you should put the following in your `config/<SNOWFLAKE_ENV>/dbt.yml` file:
```yaml
vars:
  snowflake_schema: EXAMPLE_SCHEMA
```
and then run your `dp run --env <SNOWFLAKE_ENV>` (or any similar command).

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.