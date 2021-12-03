# data-pipelines-cli

CLI for data platform

## Installation
TODO

## Usage
First, run `dp init` to configure your first template. `dp init` will allow you to add more templates later. Then, you can use `dp create <new-project-path>` to choose one of the templates added before and create the project in `<new-project-path>` directory.

`dp list` lists all added templates.

When using `dp deploy`, it will sync with your bucket provider. Provider will be chosen automatically based on the
remote URL. `dp deploy` also requires user to point to JSON or YAML file with provider-specific data like access tokens
or project names. E.g., to connect with Google Cloud Storage, one should run:
```bash
echo '{"token": "<PATH_TO_YOUR_TOKEN>", "project_name": "<YOUR_PROJECT_NAME>"}' > gs_args.json
dp deploy "gs://<YOUR_GS_PATH>" --blob-args gs_args.json
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.