"""Test function in module."""

import os

import pytest

from sphinxcontrib.versioning.lib import HandledError
from sphinxcontrib.versioning.routines import gather_git_info


def test_working(local):
    """Test with no errors.

    :param local: conftest fixture.
    """
    root, filtered_remotes = gather_git_info(str(local), [os.path.join('.', 'README')])
    assert root == str(local)
    expected = [('feature', 'heads'), ('master', 'heads'), ('annotated_tag', 'tags'), ('light_tag', 'tags')]
    assert [i[1:-1] for i in filtered_remotes] == expected


def test_simple_errors(tmpdir, caplog, local_empty):
    """Test with bad local repo and no remotes.

    :param tmpdir: pytest fixture.
    :param caplog: pytest plugin fixture.
    :param local_empty: conftest fixture.
    """
    with pytest.raises(HandledError):
        gather_git_info(str(tmpdir), ['README'])
    records = [(r.levelname, r.message) for r in caplog.records]
    assert ('CRITICAL', 'Failed to find local git repository root.') in records

    pos = len(records)
    with pytest.raises(HandledError):
        gather_git_info(str(local_empty), ['README'])
    records = [(r.levelname, r.message) for r in caplog.records][pos:]
    assert ('CRITICAL', 'Git failed to list remote refs.') in records
