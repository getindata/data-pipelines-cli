import json
from typing import Dict, Iterable, List, Optional, Union, cast

import click

from data_pipelines_cli.errors import DockerErrorResponseError


class DockerReadResponse:
    """POD representing Docker response processed by :class:`DockerResponseReader`."""

    msg: str
    """Read and processed message"""
    is_error: bool
    """Whether response is error or not"""

    def __init__(self, msg: str, is_error: bool) -> None:
        self.msg = msg
        self.is_error = is_error

    def __str__(self) -> str:
        return self.msg


class DockerResponseReader:
    """
    Read and process Docker response.

    Docker response turns into processed strings instead of plain dictionaries.
    """

    logs_generator: Iterable[Union[str, Dict[str, Union[str, Dict[str, str]]]]]
    """Iterable representing Docker response"""
    cached_read_response: Optional[List[DockerReadResponse]]
    """Internal cache of already processed response"""

    def __init__(
        self,
        logs_generator: Iterable[Union[str, Dict[str, Union[str, Dict[str, str]]]]],
    ):
        self.logs_generator = logs_generator
        self.cached_read_response = None

    def read_response(self) -> List[DockerReadResponse]:
        """
        Read and process Docker response.

        :return: List of processed lines of response
        :rtype: List[DockerReadResponse]
        """
        to_return = []

        for log in self.logs_generator:
            if isinstance(log, str):
                log = json.loads(log)
            log = cast(Dict[str, Union[str, Dict[str, str]]], log)

            if "status" in log:
                to_return.append(self._prepare_status(log))
            if "stream" in log:
                to_return += self._prepare_stream(log)
            if "aux" in log:
                to_return += self._prepare_aux(log)

            if "errorDetail" in log:
                to_return.append(self._prepare_error_detail(log))
            elif "error" in log:
                to_return.append(self._prepare_error(log))

        self.cached_read_response = to_return
        return to_return

    def click_echo_ok_responses(self) -> None:
        """Read, process and print positive Docker updates.

        :raises DockerErrorResponseError: Came across error update in Docker response.
        """
        read_response = self.cached_read_response or self.read_response()

        for response in read_response:
            if response.is_error:
                raise DockerErrorResponseError(response.msg)
            click.echo(response.msg)

    @staticmethod
    def _prepare_status(
        log: Dict[str, Union[str, Dict[str, str]]]
    ) -> DockerReadResponse:
        status_message = cast(str, log["status"])
        progress_detail = cast(str, log.get("progressDetail", ""))
        status_id = cast(str, log.get("id", ""))
        message = (
            status_message
            + (f" ({status_id})" if status_id else "")
            + (f": {progress_detail}" if progress_detail else "")
        )

        return DockerReadResponse(message, False)

    @staticmethod
    def _prepare_stream(
        log: Dict[str, Union[str, Dict[str, str]]]
    ) -> List[DockerReadResponse]:
        stream = cast(str, log["stream"])
        return list(
            map(
                lambda line: DockerReadResponse(line, False),
                filter(lambda x: x, stream.splitlines()),
            )
        )

    @staticmethod
    def _prepare_aux(
        log: Dict[str, Union[str, Dict[str, str]]]
    ) -> List[DockerReadResponse]:
        aux = cast(Dict[str, str], log["aux"])
        to_return = []
        if "Digest" in aux:
            to_return.append(DockerReadResponse(f"Digest: {aux['Digest']}", False))
        if "ID" in aux:
            to_return.append(DockerReadResponse(f"ID: {aux['ID']}", False))
        return to_return

    @staticmethod
    def _prepare_error_detail(
        log: Dict[str, Union[str, Dict[str, str]]]
    ) -> DockerReadResponse:
        error_detail = cast(Dict[str, str], log["errorDetail"])
        error_message = error_detail.get("message", "")
        error_code = error_detail.get("code", None)
        return DockerReadResponse(
            "ERROR: "
            + error_message
            + (f"\nError code: {error_code}" if error_code else ""),
            True,
        )

    @staticmethod
    def _prepare_error(
        log: Dict[str, Union[str, Dict[str, str]]]
    ) -> DockerReadResponse:
        return DockerReadResponse("ERROR: " + cast(str, log["error"]), True)
