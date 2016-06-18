"""Test objects in module."""

from subprocess import check_output, STDOUT

import pytest

from sphinxcontrib.versioning.git import get_root, GitError, list_remote
from tests import git_add_remote, git_init


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


def test_list_remote(tmpdir):
    """Test function.

    TODO: No remotes, multiple remotes, working.

    :param tmpdir: pytest fixture.
    """
    local, remote = tmpdir.ensure_dir('local'), tmpdir.ensure_dir('remote')
    git_init(local)

    # Test no remotes.
    with pytest.raises(GitError) as exc:
        list_remote(str(local))
    assert 'No remote configured to list refs from.' in exc.value.output

    # Invalid remote.
    git_add_remote(local, 'origin', str(remote))
    with pytest.raises(GitError) as exc:
        list_remote(str(local))
    assert 'does not appear to be a git repository' in exc.value.output

    # Make remote valid.
    git_init(remote, True)
    remotes = list_remote(str(local))
    assert not remotes

    # Create master branch.
    check_output(['touch', 'one.txt'], cwd=str(local), stderr=STDOUT)
    check_output(['git', 'add', 'one.txt'], cwd=str(local), stderr=STDOUT)
    check_output(['git', 'commit', '-m', 'one'], cwd=str(local), stderr=STDOUT)
    check_output(['git', 'push', 'origin', 'master'], cwd=str(local), stderr=STDOUT)
    remotes = list_remote(str(local))
    assert [i[1:] for i in remotes] == [['master', 'heads']]

    # Setup branch and tag.
    check_output(['git', 'tag', 'v1.2'], cwd=str(local), stderr=STDOUT)
    check_output(['git', 'tag', '--annotate', '-m', 'an-tag', 'v2.1'], cwd=str(local), stderr=STDOUT)
    check_output(['git', 'checkout', '-b', 'feature'], cwd=str(local), stderr=STDOUT)
    remotes = list_remote(str(local))
    assert [i[1:] for i in remotes] == [['master', 'heads']]
    check_output(['git', 'push', 'origin', 'v1.2', 'v2.1', 'feature'], cwd=str(local), stderr=STDOUT)
    remotes = list_remote(str(local))
    assert [i[1:] for i in remotes] == [['feature', 'heads'], ['master', 'heads'], ['v1.2', 'tags'], ['v2.1', 'tags']]

    # Add other remote.
    remote2 = tmpdir.ensure_dir('remote2')
    git_init(remote2, True)
    git_add_remote(local, 'remote2', str(remote2))
    check_output(['git', 'push', 'remote2', 'v1.2'], cwd=str(local), stderr=STDOUT)
    remotes = list_remote(str(local))
    assert [i[1:] for i in remotes] == [['feature', 'heads'], ['master', 'heads'], ['v1.2', 'tags'], ['v2.1', 'tags']]

    # Remove origin but not other remotes.
    check_output(['git', 'remote', 'rm', 'origin'], cwd=str(local), stderr=STDOUT)
    with pytest.raises(GitError) as exc:
        list_remote(str(local))
    assert 'No remote configured to list refs from' in exc.value.output
