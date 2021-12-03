import os
from typing import Dict, Optional, Set, Union

import fsspec
from fsspec import AbstractFileSystem


# -------------------------------- Synchronize --------------------------------
class LocalRemoteSync:
    local_fs: AbstractFileSystem
    local_path_str: str
    remote_path_str: str
    _local_directory_suffixes: Optional[Set[str]]

    def __init__(
        self,
        local_path: Union[str, os.PathLike],
        remote_path: str,
        remote_kwargs: Dict[str, str],
    ):
        self.local_path_str = str(local_path).rstrip("/")
        self.local_fs = fsspec.filesystem("file")
        self.remote_fs, self.remote_path_str = fsspec.core.url_to_fs(
            remote_path, **remote_kwargs
        )
        self._local_directory_suffixes = None

    def sync(self, delete: bool = True):
        self._push_sync()
        if delete:
            self._delete()

    def _push_sync(self):
        """Push every file to the remote"""

        # TODO: Is it "lazy" (checking what to update) or not?
        local_directory = self.local_fs.find(self.local_path_str)
        self._local_directory_suffixes = set()
        for local_file in local_directory:
            local_file_suffix = local_file[len(self.local_path_str) :]
            self._local_directory_suffixes.add(local_file_suffix)
            self.remote_fs.put_file(
                local_file, self.remote_path_str + local_file_suffix
            )

    def _delete(self):
        """Remove every file from remote that's not local"""
        remote_directory = self.remote_fs.find(self.remote_path_str)
        for remote_file in remote_directory:
            remote_file_suffix = remote_file[len(self.remote_path_str) :]
            if remote_file_suffix not in self._local_directory_suffixes:
                self.remote_fs.rm(remote_file)
