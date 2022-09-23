from typing import Optional


class DataPipelinesError(Exception):
    """Base class for all exceptions in data_pipelines_cli module"""

    message: str
    """explanation of the error"""
    submessage: Optional[str]
    """additional informations for the error"""

    def __init__(self, message: str, submessage: Optional[str] = None) -> None:
        self.message = message
        self.submessage = submessage


class DependencyNotInstalledError(DataPipelinesError):
    """Exception raised if certain dependency is not installed"""

    def __init__(self, program_name: str) -> None:
        super().__init__(
            f"'{program_name}' not installed. Run 'pip install "
            f"data-pipelines-cli[{program_name}]'"
        )


class NoConfigFileError(DataPipelinesError):
    """Exception raised if `.dp.yml` does not exist"""

    def __init__(self) -> None:
        super().__init__("`.dp.yml` config file does not exists. Run 'dp init' to create it.")


class NotAProjectDirectoryError(DataPipelinesError):
    """Exception raised if `.copier-answers.yml` file does not exist in given dir"""

    def __init__(self, project_path: str) -> None:
        super().__init__(
            f"Given path {project_path} is not a data-pipelines project directory."
            " Run 'dp create' first to create a project"
        )


class SubprocessNonZeroExitError(DataPipelinesError):
    """Exception raised if subprocess exits with non-zero exit code"""

    def __init__(
        self, subprocess_name: str, exit_code: int, subprocess_output: Optional[str] = None
    ) -> None:
        super().__init__(
            f"{subprocess_name} has exited with non-zero exit code: {exit_code}",
            submessage=subprocess_output,
        )


class SubprocessNotFound(DataPipelinesError):
    """Exception raised if subprocess cannot be found"""

    def __init__(self, subprocess_name: str) -> None:
        super().__init__(
            f"{subprocess_name} cannot be found. "
            "Ensure it is installed and listed in your $PATH."
        )


class DockerNotInstalledError(DependencyNotInstalledError):
    """Exception raised if 'docker' is not installed"""

    def __init__(self) -> None:
        super().__init__("docker")


class JinjaVarKeyError(DataPipelinesError):
    def __init__(self, key: str) -> None:
        super().__init__(
            f"Variable '{key}' cannot be found neither in 'dbt.yml' and "
            "'$HOME/.dp.yml' vars nor in environment variables, causing Jinja "
            "template rendering to fail."
        )


class AirflowDagsPathKeyError(DataPipelinesError):
    """Exception raised if there is no ``dags_path`` in `airflow.yml` file."""

    def __init__(self) -> None:
        super().__init__("Variable 'dags_path' cannot be found in 'airflow.yml' config file.")


class DockerErrorResponseError(DataPipelinesError):
    """Exception raised if there is an error response from Docker client."""

    def __init__(self, error_msg: str) -> None:
        super().__init__("Error raised when using Docker.\n" + error_msg)


class NotSuppertedBIError(DataPipelinesError):
    """Exception raised if there is no ``target_id`` in `bi.yml`"""

    def __init__(self) -> None:
        super().__init__(
            "Variable 'target_id' cannot be found in 'bi.yml' "
            "config file or the value not matched supported solutions."
        )
