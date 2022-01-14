from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Optional, Union

import click


# Python's `sed` equivalent, based on the following answer:
# https://stackoverflow.com/a/31499114
def replace(
    filename: Union[str, os.PathLike[str]], pattern: str, replacement: str
) -> None:
    """
    Perform the pure-Python equivalent of in-place `sed` substitution: e.g.,
    ``sed -i -e 's/'${pattern}'/'${replacement}' "${filename}"``.

    Beware however, it uses Python regex dialect instead of `sed`'s one.
    It can introduce regex-related bugs.
    """
    # For efficiency, precompile the passed regular expression.
    pattern_compiled = re.compile(pattern)

    # For portability, NamedTemporaryFile() defaults to mode "w+b" (i.e.,
    # binary writing with updating). This is usually a good thing. In this
    # case, however, binary writing imposes non-trivial encoding constraints
    # trivially resolved by switching to text writing. Let's do that.
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
        with open(filename) as src_file:
            for line in src_file:
                tmp_file.write(pattern_compiled.sub(replacement, line))

    # Overwrite the original file with the munged temporary file in a
    # manner preserving file attributes (e.g., permissions).
    shutil.copystat(filename, tmp_file.name)
    shutil.move(tmp_file.name, filename)


def git_revision_hash() -> Optional[str]:
    """
    Get current Git revision hash, if Git is installed and any revision exists.

    :return: Git revision hash, if possible.
    :rtype: Optional[str]
    """
    try:
        rev_process = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True
        )
        return rev_process.stdout.decode("ascii").strip()
    except FileNotFoundError:
        click.echo(
            "The tool has run across an error when trying to get Git "
            "revision hash. Ensure you have `git` installed",
            file=sys.stderr,
        )
        return None
    except subprocess.CalledProcessError as err:
        click.echo(
            "The tool has run across a following error when trying to "
            "get Git revision hash:",
            file=sys.stderr,
        )
        click.echo(err.stderr, file=sys.stderr)
        return None
