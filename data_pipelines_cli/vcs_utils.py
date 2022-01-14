"""Utilities related to VCS."""

from copier.vcs import GIT_PREFIX


def add_suffix_to_git_template_path(template_path: str) -> str:
    """Add ``.git`` suffix to *template_path*, if necessary.

    Check if *template_path* starts with Git-specific prefix (e.g. `git://`),
    or `http://` or `https://` protocol. If so, then add ``.git`` suffix if
    not present. Does nothing otherwise (as *template_path* probably points to
    a local directory).

    :param template_path: Path or URI to Git-based repository
    :type template_path: str
    :return: *template_path* with ``.git`` as suffix, if necessary
    :rtype: str
    """
    if not template_path.startswith(GIT_PREFIX) and not template_path.startswith(
        ("http://", "https://")
    ):
        return template_path
    return template_path + ("" if template_path.endswith(".git") else ".git")
