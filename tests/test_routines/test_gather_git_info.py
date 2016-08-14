"""Test function in module."""

import os

import pytest

from sphinxcontrib.versioning.lib import HandledError
from sphinxcontrib.versioning.routines import gather_git_info


def test_working(local):
    """Test with no errors.

    :param local: conftest fixture.
    """
    filtered_remotes = gather_git_info(str(local), [os.path.join('.', 'README')], tuple(), tuple())
    expected = [['feature', 'heads'], ['master', 'heads'], ['annotated_tag', 'tags'], ['light_tag', 'tags']]
    assert [i[1:-2] for i in filtered_remotes] == expected


@pytest.mark.parametrize('wlb', [False, True])
@pytest.mark.parametrize('wlt', [False, True])
def test_whitelisting(local, wlb, wlt):
    """Test whitelisting either or or neither.

    :param local: conftest fixture.
    :param bool wlb: Whitelist branches.
    :param bool wlt: Whitelist tags.
    """
    whitelist_branches = tuple()
    whitelist_tags = tuple()
    expected = list()

    expected.append(['feature', 'heads'])
    if wlb:
        whitelist_branches = ('feature',)
    else:
        expected.append(['master', 'heads'])

    expected.append(['annotated_tag', 'tags'])
    if wlt:
        whitelist_tags = ('annotated',)
    else:
        expected.append(['light_tag', 'tags'])

    filtered_remotes = gather_git_info(str(local), [os.path.join('.', 'README')], whitelist_branches, whitelist_tags)
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
            gather_git_info(str(local), ['README'], tuple(), tuple())
    else:
        filtered_remotes = gather_git_info(str(local), ['README'], tuple(), tuple())
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


def test_failed_list(caplog, local_empty):
    """Test error.

    :param caplog: pytest plugin fixture.
    :param local_empty: conftest fixture.
    """
    with pytest.raises(HandledError):
        gather_git_info(str(local_empty), ['README'], tuple(), tuple())
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
        gather_git_info(str(local), ['README'], tuple(), tuple())
    records = [(r.levelname, r.message) for r in caplog.records]
    assert ('ERROR', 'Failed to get dates for all remote commits.') in records
