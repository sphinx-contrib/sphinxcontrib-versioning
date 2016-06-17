"""Test objects in module."""

import pytest

from sphinxcontrib.versioning.git import get_root, GitError
from tests import git_init


def test_get_root(tmpdir):
    """Test function.

    :param tmpdir: pytest fixture.
    """
    # Test failure.
    with pytest.raises(GitError):
        get_root(str(tmpdir))

    # Initialize.
    git_init(tmpdir)

    # Test root.
    assert get_root(str(tmpdir)) == str(tmpdir)

    # Test subdir.
    subdir = tmpdir.ensure_dir('subdir')
    assert get_root(str(subdir)) == str(tmpdir)
