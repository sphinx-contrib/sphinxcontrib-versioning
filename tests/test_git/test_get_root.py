"""Test function in module."""

import pytest

from sphinxcontrib.versioning.git import get_root, GitError


def test(tmpdir, local_empty):
    """Test function.

    :param tmpdir: pytest fixture.
    :param local_empty: conftest fixture.
    """
    # Test failure.
    with pytest.raises(GitError):
        get_root(str(tmpdir))

    # Test root.
    assert get_root(str(local_empty)) == str(local_empty)

    # Test subdir.
    subdir = local_empty.ensure_dir('subdir')
    assert get_root(str(subdir)) == str(local_empty)
