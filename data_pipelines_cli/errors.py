class DataPipelinesError(Exception):
    """Base class for all exceptions in data_pipelines_cli module"""

    message: str
    """explanation of the error"""

    def __init__(self, message: str) -> None:
        self.message = message


class DependencyNotInstalledError(DataPipelinesError):
    """Exception raised if certain dependency is not installed"""

    def __init__(self, program_name: str) -> None:
        self.message = (
            f"'{program_name}' not installed. Run 'pip install "
            f"data-pipelines-cli[{program_name}]'"
        )


class NoConfigFileError(DataPipelinesError):
    """Exception raised if `.dp.yml` does not exist"""

    def __init__(self) -> None:
        self.message = "`.dp.yml` config file does not exists"


class SubprocessNonZeroExitError(DataPipelinesError):
    """Exception raised if subprocess exits with non-zero exit code"""

    def __init__(self, subprocess_name: str, exit_code: int) -> None:
        self.message = (
            f"{subprocess_name} has exited with non-zero exit code: {exit_code}"
        )


class DockerNotInstalledError(DependencyNotInstalledError):
    """Exception raised if 'docker' is not installed"""

    def __init__(self) -> None:
        super().__init__("docker")
