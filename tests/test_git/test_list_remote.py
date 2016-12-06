"""Test function in module."""

import pytest

from sphinxcontrib.versioning.git import GitError, list_remote


def test_bad_remote(tmpdir, local_empty):
    """Test with no/invalid remote.

    :param tmpdir: pytest fixture.
    :param local_empty: conftest fixture.
    """
    # Test no remotes.
    with pytest.raises(GitError) as exc:
        list_remote(str(local_empty))
    assert 'No remote configured to list refs from.' in exc.value.output

    # Test wrong name.
    pytest.run(local_empty, ['git', 'remote', 'add', 'something', tmpdir.ensure_dir('empty')])
    with pytest.raises(GitError) as exc:
        list_remote(str(local_empty))
    assert 'No remote configured to list refs from.' in exc.value.output

    # Invalid remote.
    pytest.run(local_empty, ['git', 'remote', 'rename', 'something', 'origin'])
    with pytest.raises(GitError) as exc:
        list_remote(str(local_empty))
    assert 'does not appear to be a git repository' in exc.value.output


def test_empty_remote(local_commit, remote):
    """Test with valid but empty remote.

    :param local_commit: conftest fixture.
    :param remote: conftest fixture.
    """
    pytest.run(local_commit, ['git', 'remote', 'add', 'origin', remote])
    remotes = list_remote(str(local_commit))
    assert not remotes

    # Push.
    pytest.run(local_commit, ['git', 'push', 'origin', 'master'])
    remotes = list_remote(str(local_commit))
    assert [i[1:] for i in remotes] == [['master', 'heads']]


def test_branch_tags(local):
    """Test with branches and tags.

    :param local: conftest fixture.
    """
    sha = pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip()
    remotes = list_remote(str(local))
    expected = [
        [sha, 'feature', 'heads'],
        [sha, 'master', 'heads'],
        [sha, 'annotated_tag', 'tags'],
        [sha, 'light_tag', 'tags'],
    ]
    assert remotes == expected

    # New commit to master locally.
    local.join('README').write('changed')
    pytest.run(local, ['git', 'commit', '-am', 'Changed'])
    remotes = list_remote(str(local))
    assert remotes == expected

    # Push.
    pytest.run(local, ['git', 'push', 'origin', 'master'])
    sha2 = pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip()
    remotes = list_remote(str(local))
    expected = [
        [sha, 'feature', 'heads'],
        [sha2, 'master', 'heads'],
        [sha, 'annotated_tag', 'tags'],
        [sha, 'light_tag', 'tags'],
    ]
    assert remotes == expected


def test_outdated_local(tmpdir, local, remote):
    """Test with remote changes not pulled.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param remote: conftest fixture.
    """
    # Setup separate local repo now before pushing changes to it from the primary local repo.
    local_outdated = tmpdir.ensure_dir('local_outdated')
    pytest.run(local_outdated, ['git', 'clone', '--branch', 'master', remote, '.'])
    sha = pytest.run(local_outdated, ['git', 'rev-parse', 'HEAD']).strip()
    remotes = list_remote(str(local_outdated))
    expected = [
        [sha, 'feature', 'heads'],
        [sha, 'master', 'heads'],
        [sha, 'annotated_tag', 'tags'],
        [sha, 'light_tag', 'tags'],
    ]
    assert remotes == expected

    # Make changes from primary local and push to common remote.
    local.join('README').write('changed')
    pytest.run(local, ['git', 'commit', '-am', 'Changed'])
    pytest.run(local, ['git', 'push', 'origin', 'master'])
    sha2 = pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip()
    remotes = list_remote(str(local))
    expected = [
        [sha, 'feature', 'heads'],
        [sha2, 'master', 'heads'],
        [sha, 'annotated_tag', 'tags'],
        [sha, 'light_tag', 'tags'],
    ]
    assert remotes == expected

    # Run list_remote() on outdated repo and verify it still gets latest refs.
    remotes = list_remote(str(local_outdated))
    assert remotes == expected
