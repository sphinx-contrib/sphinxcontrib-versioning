"""Test function in module."""

import time

import pytest

from sphinxcontrib.versioning.git import filter_and_date, GitError, list_remote

BEFORE = int(time.time())


def test_one_commit(local):
    """Test with one commit.

    :param local: conftest fixture.
    """
    sha = pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip()
    dates = filter_and_date(str(local), ['does_not_exist'], [sha])
    assert not dates

    with pytest.raises(GitError):
        filter_and_date(str(local), ['README'], ['invalid'])

    # Test with existing conf_rel_path.
    dates = filter_and_date(str(local), ['README'], [sha])
    assert list(dates) == [sha]
    assert dates[sha][0] >= BEFORE
    assert dates[sha][0] < time.time()
    assert dates[sha][1] == 'README'

    # Test duplicate SHAs.
    dates2 = filter_and_date(str(local), ['README'], [sha, sha, sha])
    assert dates2 == dates


def test_three_commits_multiple_paths(local):
    """Test with two valid candidates and one ignored candidate.

    :param local: conftest fixture.
    """
    shas = {pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip()}
    pytest.run(local, ['git', 'checkout', 'feature'])
    local.ensure('conf.py').write('pass\n')
    pytest.run(local, ['git', 'add', 'conf.py'])
    pytest.run(local, ['git', 'commit', '-m', 'root'])
    shas.add(pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip())
    pytest.run(local, ['git', 'checkout', '-b', 'subdir', 'master'])
    local.ensure('docs', 'conf.py').write('pass\n')
    pytest.run(local, ['git', 'add', 'docs/conf.py'])
    pytest.run(local, ['git', 'commit', '-m', 'subdir'])
    shas.add(pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip())
    pytest.run(local, ['git', 'push', 'origin', 'feature', 'subdir'])

    assert len(shas) == 3
    dates = filter_and_date(str(local), ['conf.py', 'docs/conf.py'], shas)
    assert len(dates) == 2


def test_multiple_commits(local):
    """Test with multiple commits.

    :param local: conftest fixture.
    """
    shas = {pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip()}
    for _ in range(50):
        local.ensure('docs', 'conf.py').write('pass\n')
        pytest.run(local, ['git', 'add', 'docs/conf.py'])
        pytest.run(local, ['git', 'commit', '-m', 'add'])
        shas.add(pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip())
        pytest.run(local, ['git', 'rm', 'docs/conf.py'])
        pytest.run(local, ['git', 'commit', '-m', 'remove'])
        shas.add(pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip())
    assert len(shas) == 101
    dates = filter_and_date(str(local), ['docs/conf.py'], list(shas))
    assert len(dates) == 50


def test_outdated_local(tmpdir, local, remote):
    """Test with remote changes not pulled.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param remote: conftest fixture.
    """
    # Commit to separate local repo and push to common remote.
    local_ahead = tmpdir.ensure_dir('local_ahead')
    pytest.run(local_ahead, ['git', 'clone', remote, '.'])
    local_ahead.join('README').write('changed')
    pytest.run(local_ahead, ['git', 'commit', '-am', 'Changed master'])
    pytest.run(local_ahead, ['git', 'checkout', 'feature'])
    local_ahead.join('README').write('changed')
    pytest.run(local_ahead, ['git', 'commit', '-am', 'Changed feature'])
    pytest.run(local_ahead, ['git', 'push', 'origin', 'master', 'feature'])

    # Commits not fetched.
    remotes = list_remote(str(local))
    shas = [r[0] for r in remotes]
    with pytest.raises(GitError):
        filter_and_date(str(local), ['README'], shas)

    # Pull and retry.
    pytest.run(local, ['git', 'pull', 'origin', 'master'])
    pytest.run(local, ['git', 'checkout', 'feature'])
    pytest.run(local, ['git', 'pull', 'origin', 'feature'])
    dates = filter_and_date(str(local), ['README'], shas)
    assert len(dates) == 3  # Original SHA is the same for everything. Plus above two commits.
