"""Test function in module."""

import pytest

from sphinxcontrib.versioning.git import fetch_commits, filter_and_date, GitError, list_remote


def test_fetch_existing(local, run):
    """Fetch commit that is already locally available.

    :param local: conftest fixture.
    :param run: conftest fixture.
    """
    remotes = list_remote(str(local))
    fetch_commits(str(local), remotes)
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])  # Exit 0 if nothing changed.


@pytest.mark.usefixtures('outdate_local')
@pytest.mark.parametrize('clone_branch', [False, True])
def test_fetch_new(local, local_light, run, clone_branch):
    """Fetch new commits.

    :param local: conftest fixture.
    :param local_light: conftest fixture.
    :param run: conftest fixture.
    :param bool clone_branch: Test with local repo cloned with --branch.
    """
    # Setup other behind local with just one cloned branch.
    if clone_branch:
        local = local_light

    # Get SHAs and verify not fetched.
    remotes = list_remote(str(local))
    assert len(remotes) == 7  # master feature light_tag annotated_tag nb_tag orphaned_branch ob_at
    shas = {r[0] for r in remotes}
    assert len(shas) == 3
    with pytest.raises(GitError):
        filter_and_date(str(local), ['README'], shas)

    # Fetch and verify.
    fetch_commits(str(local), remotes)
    dates = filter_and_date(str(local), ['README'], shas)
    assert len(dates) == 3
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])


@pytest.mark.usefixtures('outdate_local')
@pytest.mark.parametrize('clone_branch', [False, True])
def test_new_branch_tags(local, local_light, run, clone_branch):
    """Test with new branches and tags unknown to local repo.

    :param local: conftest fixture.
    :param local_light: conftest fixture.
    :param run: conftest fixture.
    :param bool clone_branch: Test with local repo cloned with --branch.
    """
    if clone_branch:
        local = local_light

    # Get SHAs and verify not fetched.
    remotes = list_remote(str(local))
    assert len(remotes) == 7  # master feature light_tag annotated_tag nb_tag orphaned_branch ob_at
    shas = {r[0] for r in remotes}
    assert len(shas) == 3
    with pytest.raises(GitError):
        filter_and_date(str(local), ['README'], shas)

    # Fetch and verify.
    fetch_commits(str(local), remotes)
    dates = filter_and_date(str(local), ['README'], shas)
    assert len(dates) == 3
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])
