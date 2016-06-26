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


@pytest.mark.parametrize('clone_branch', [False, True])
def test_fetch_new(tmpdir, local, remote, run, clone_branch):
    """Fetch new commits.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param remote: conftest fixture.
    :param run: conftest fixture.
    :param bool clone_branch: Test with local repo cloned with --branch.
    """
    # Setup other behind local with just one cloned branch.
    if clone_branch:
        local = tmpdir.ensure_dir('local2')
        run(local, ['git', 'clone', '--depth=1', '--branch=feature', remote, '.'])
        sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()
        run(local, ['git', 'checkout', '-qf', sha])

    # Commit to separate local repo and push to common remote.
    local_ahead = tmpdir.ensure_dir('local_ahead')
    run(local_ahead, ['git', 'clone', remote, '.'])
    local_ahead.join('README').write('changed')
    run(local_ahead, ['git', 'commit', '-am', 'Changed master'])
    run(local_ahead, ['git', 'checkout', 'feature'])
    local_ahead.join('README').write('changed')
    run(local_ahead, ['git', 'commit', '-am', 'Changed feature'])
    run(local_ahead, ['git', 'push', 'origin', 'master', 'feature'])

    # Get SHAs and verify not fetched.
    remotes = list_remote(str(local))
    assert len(remotes) == 4  # master feature light_tag annotated_tag
    shas = {r[0] for r in remotes}
    assert len(shas) == 3
    with pytest.raises(GitError):
        filter_and_date(str(local), ['README'], shas)

    # Fetch and verify.
    fetch_commits(str(local), remotes)
    dates = filter_and_date(str(local), ['README'], shas)
    assert len(dates) == 3
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])


@pytest.mark.parametrize('clone_branch', [False, True])
def test_new_branch_tags(tmpdir, local, remote, run, clone_branch):
    """Test with new branches and tags unknown to local repo.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param remote: conftest fixture.
    :param run: conftest fixture.
    :param bool clone_branch: Test with local repo cloned with --branch.
    """
    # Setup other behind local with just one cloned branch.
    if clone_branch:
        local = tmpdir.ensure_dir('local2')
        run(local, ['git', 'clone', '--depth=1', '--branch=feature', remote, '.'])
        sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()
        run(local, ['git', 'checkout', '-qf', sha])

    # Commit to separate local repo and push to common remote.
    local_ahead = tmpdir.ensure_dir('local_ahead')
    run(local_ahead, ['git', 'clone', remote, '.'])
    run(local_ahead, ['git', 'checkout', '-b', 'un_pushed_branch'])
    local_ahead.join('README').write('changed')
    run(local_ahead, ['git', 'commit', '-am', 'Changed new branch'])
    run(local_ahead, ['git', 'tag', 'nb_tag'])
    run(local_ahead, ['git', 'checkout', '--orphan', 'orphaned_branch'])
    local_ahead.join('README').write('new')
    run(local_ahead, ['git', 'add', 'README'])
    run(local_ahead, ['git', 'commit', '-m', 'Added new README'])
    run(local_ahead, ['git', 'tag', '--annotate', '-m', 'Tag annotation.', 'ob_at'])
    run(local_ahead, ['git', 'push', 'origin', 'nb_tag', 'orphaned_branch', 'ob_at'])

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
