from __future__ import annotations

import os
from typing import Dict, Set, Union

import fsspec
from fsspec import AbstractFileSystem

from .cli_utils import echo_subinfo


class LocalRemoteSync:
    local_fs: AbstractFileSystem
    local_path_str: str
    remote_path_str: str
    _local_directory_suffixes: Set[str]

    def __init__(
        self,
        local_path: Union[str, os.PathLike[str]],
        remote_path: str,
        remote_kwargs: Dict[str, str],
    ):
        self.local_path_str = str(local_path).rstrip("/")
        self.local_fs = fsspec.filesystem("file")
        self.remote_fs, self.remote_path_str = fsspec.core.url_to_fs(
            remote_path.rstrip("/"), **remote_kwargs
        )
        self._local_directory_suffixes = set()

    def sync(self, delete: bool = True) -> None:
        self._push_sync()
        if delete:
            self._delete()

    def _push_sync(self) -> None:
        """Push every file to the remote"""

        # TODO: Is it "lazy" (checking what to update) or not?
        local_directory = self.local_fs.find(self.local_path_str)
        self._local_directory_suffixes = set()
        for local_file in local_directory:
            local_file_suffix = local_file[len(self.local_path_str) :]
            self._local_directory_suffixes.add(local_file_suffix)
            remote_path_with_suffix = self.remote_path_str + local_file_suffix
            echo_subinfo(f"- Pushing {str(local_file)} to {remote_path_with_suffix}")
            self.remote_fs.put_file(local_file, remote_path_with_suffix)

    def _delete(self) -> None:
        """Remove every file from remote that's not local"""
        remote_directory = self.remote_fs.find(self.remote_path_str)
        for remote_file in remote_directory:
            remote_file_suffix = remote_file[len(self.remote_path_str) :]
            if remote_file_suffix not in self._local_directory_suffixes:
                self.remote_fs.rm(remote_file)
