"""pytest fixtures for this directory."""

import pytest

from sphinxcontrib.versioning.git import run_command


@pytest.fixture
def run():
    """run_command() wrapper returned from a pytest fixture."""
    return lambda d, c: run_command(str(d), [str(i) for i in c])


@pytest.fixture
def local_empty(tmpdir, run):
    """Local git repository with no commits.

    :param tmpdir: pytest fixture.
    :param run: local fixture.

    :return: Path to repo root.
    :rtype: py.path
    """
    repo = tmpdir.ensure_dir('local')
    run(repo, ['git', 'init'])
    return repo


@pytest.fixture
def remote(tmpdir, run):
    """Remote git repository with nothing pushed to it.

    :param tmpdir: pytest fixture.
    :param run: local fixture.

    :return: Path to bare repo root.
    :rtype: py.path
    """
    repo = tmpdir.ensure_dir('remote')
    run(repo, ['git', 'init', '--bare'])
    return repo


@pytest.fixture
def local_commit(local_empty, run):
    """Local git repository with one commit.

    :param local_empty: local fixture.
    :param run: local fixture.

    :return: Path to repo root.
    :rtype: py.path
    """
    local_empty.join('README').write('Dummy readme file.')
    run(local_empty, ['git', 'add', 'README'])
    run(local_empty, ['git', 'commit', '-m', 'Initial commit.'])
    return local_empty


@pytest.fixture
def local(local_commit, remote, run):
    """Local git repository with branches, light tags, and annotated tags pushed to remote.

    :param local_commit: local fixture.
    :param remote: local fixture.
    :param run: local fixture.

    :return: Path to repo root.
    :rtype: py.path
    """
    run(local_commit, ['git', 'tag', 'light_tag'])
    run(local_commit, ['git', 'tag', '--annotate', '-m', 'Tag annotation.', 'annotated_tag'])
    run(local_commit, ['git', 'checkout', '-b', 'feature'])
    run(local_commit, ['git', 'checkout', 'master'])
    run(local_commit, ['git', 'remote', 'add', 'origin', remote])
    run(local_commit, ['git', 'push', 'origin', 'master', 'feature', 'light_tag', 'annotated_tag'])
    return local_commit
