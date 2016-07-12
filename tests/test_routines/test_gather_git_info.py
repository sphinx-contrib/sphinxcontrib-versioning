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
    expected = [['feature', 'heads'], ['master', 'heads'], ['annotated_tag', 'tags'], ['light_tag', 'tags']]
    assert [i[1:-2] for i in filtered_remotes] == expected


@pytest.mark.usefixtures('outdate_local')
@pytest.mark.parametrize('skip_fetch', [False, True])
def test_fetch(monkeypatch, caplog, local, skip_fetch):
    """Test with fetch required.

    :param monkeypatch: pytest fixture.
    :param caplog: pytest plugin fixture.
    :param local: conftest fixture.
    :param bool skip_fetch: Patch fetch_commits().
    """
    if skip_fetch:
        monkeypatch.setattr('sphinxcontrib.versioning.routines.fetch_commits', lambda *args: args)
        with pytest.raises(HandledError):
            gather_git_info(str(local), ['README'])
    else:
        root, filtered_remotes = gather_git_info(str(local), ['README'])
        assert root == str(local)
        expected = [
            ['feature', 'heads'],
            ['master', 'heads'],
            ['orphaned_branch', 'heads'],
            ['annotated_tag', 'tags'],
            ['light_tag', 'tags'],
            ['nb_tag', 'tags'],
            ['ob_at', 'tags'],
        ]
        assert [i[1:-2] for i in filtered_remotes] == expected

    records = [(r.levelname, r.message) for r in caplog.records]
    assert ('INFO', 'Need to fetch from remote...') in records


def test_bad_path(tmpdir, caplog):
    """Test error.

    :param tmpdir: pytest fixture.
    :param caplog: pytest plugin fixture.
    """
    with pytest.raises(HandledError):
        gather_git_info(str(tmpdir.join('unknown')), ['README'])
    records = [(r.levelname, r.message) for r in caplog.records]
    assert ('ERROR', 'Path not found: {}'.format(tmpdir.join('unknown'))) in records

    with pytest.raises(HandledError):
        gather_git_info(str(tmpdir.ensure('is_file')), ['README'])
    records = [(r.levelname, r.message) for r in caplog.records][len(records):]
    assert ('ERROR', 'Path not a directory: {}'.format(tmpdir.join('is_file'))) in records


def test_not_git_root(tmpdir, caplog):
    """Test error.

    :param tmpdir: pytest fixture.
    :param caplog: pytest plugin fixture.
    """
    with pytest.raises(HandledError):
        gather_git_info(str(tmpdir), ['README'])
    records = [(r.levelname, r.message) for r in caplog.records]
    assert ('ERROR', 'Failed to find local git repository root.') in records


def test_failed_list(caplog, local_empty):
    """Test error.

    :param caplog: pytest plugin fixture.
    :param local_empty: conftest fixture.
    """
    with pytest.raises(HandledError):
        gather_git_info(str(local_empty), ['README'])
    records = [(r.levelname, r.message) for r in caplog.records]
    assert ('ERROR', 'Git failed to list remote refs.') in records


def test_cpe(monkeypatch, tmpdir, caplog, local, run):
    """Test unexpected git error (network issue, etc).

    :param monkeypatch: pytest fixture.
    :param tmpdir: pytest fixture.
    :param caplog: pytest plugin fixture.
    :param local: conftest fixture.
    :param run: conftest fixture.
    """
    command = ['git', 'status']
    monkeypatch.setattr('sphinxcontrib.versioning.routines.filter_and_date', lambda *_: run(str(tmpdir), command))

    with pytest.raises(HandledError):
        gather_git_info(str(local), ['README'])
    records = [(r.levelname, r.message) for r in caplog.records]
    assert ('ERROR', 'Failed to get dates for all remote commits.') in records
