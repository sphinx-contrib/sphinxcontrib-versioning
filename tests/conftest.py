"""pytest fixtures for this directory."""

import re

import pytest

from sphinxcontrib.versioning.git import run_command
from sphinxcontrib.versioning.lib import Config

RE_URLS = re.compile('<li><a href="[^"]+">[^<]+</a></li>')


@pytest.fixture
def config(monkeypatch):
    """Mock config from Click context.

    :param monkeypatch: pytest fixture.

    :return: Config instance.
    :rtype: sphinxcontrib.versioning.lib.Config
    """
    instance = Config()
    ctx = type('', (), {'find_object': staticmethod(lambda _: instance)})
    monkeypatch.setattr('click.get_current_context', lambda: ctx)
    return instance


@pytest.fixture
def run():
    """run_command() wrapper returned from a pytest fixture."""
    return lambda d, c: run_command(str(d), [str(i) for i in c])


@pytest.fixture
def urls():
    """Verify URLs in HTML file match expected."""
    def match(path, expected):
        """Assert equals and return file contents.

        :param py.path path: Path to file to read.
        :param list expected: Expected matches.

        :return: File contents.
        :rtype: str
        """
        contents = path.read()
        actual = RE_URLS.findall(contents)
        assert actual == expected
        return contents
    return match


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


@pytest.fixture
def local_light(tmpdir, local, remote, run):
    """Light-weight local repository similar to how Travis/AppVeyor clone repos.

    :param tmpdir: pytest fixture.
    :param local: local fixture.
    :param remote: local fixture.
    :param run: local fixture.

    :return: Path to repo root.
    :rtype: py.path
    """
    assert local  # Ensures local pushes feature branch before this fixture is called.
    local2 = tmpdir.ensure_dir('local2')
    run(local2, ['git', 'clone', '--depth=1', '--branch=feature', remote, '.'])
    sha = run(local2, ['git', 'rev-parse', 'HEAD']).strip()
    run(local2, ['git', 'checkout', '-qf', sha])

    return local2


@pytest.fixture
def outdate_local(tmpdir, local_light, remote, run):
    """Clone remote to other directory and push changes. Causes `local` fixture to be outdated.

    :param tmpdir: pytest fixture.
    :param local_light: local fixture.
    :param remote: local fixture.
    :param run: local fixture.

    :return: Path to repo root.
    :rtype: py.path
    """
    assert local_light  # Ensures local_light is setup before this fixture pushes to remote.
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
    return local_ahead


@pytest.fixture
def local_docs(local, run):
    """Local repository with Sphinx doc files. Pushed to remote.

    :param local: local fixture.
    :param run: local fixture.

    :return: Path to repo root.
    :rtype: py.path
    """
    local.ensure('conf.py')
    local.join('contents.rst').write(
        'Test\n'
        '====\n'
        '\n'
        'Sample documentation.\n'
        '\n'
        '.. toctree::\n'
        '    one\n'
        '    two\n'
        '    three\n'
    )
    local.join('one.rst').write(
        '.. _one:\n'
        '\n'
        'One\n'
        '===\n'
        '\n'
        'Sub page documentation 1.\n'
    )
    local.join('two.rst').write(
        '.. _two:\n'
        '\n'
        'Two\n'
        '===\n'
        '\n'
        'Sub page documentation 2.\n'
    )
    local.join('three.rst').write(
        '.. _three:\n'
        '\n'
        'Three\n'
        '=====\n'
        '\n'
        'Sub page documentation 3.\n'
    )
    run(local, ['git', 'add', 'conf.py', 'contents.rst', 'one.rst', 'two.rst', 'three.rst'])
    run(local, ['git', 'commit', '-m', 'Adding docs.'])
    run(local, ['git', 'push', 'origin', 'master'])
    return local


@pytest.fixture
def local_docs_ghp(local_docs, run):
    """Add an orphaned branch to remote.

    :param local_docs: local fixture.
    :param run: local fixture.
    """
    run(local_docs, ['git', 'checkout', '--orphan', 'gh-pages'])
    run(local_docs, ['git', 'rm', '-rf', '.'])
    local_docs.join('README').write('Orphaned branch for HTML docs.')
    run(local_docs, ['git', 'add', 'README'])
    run(local_docs, ['git', 'commit', '-m', 'Initial Commit'])
    run(local_docs, ['git', 'push', 'origin', 'gh-pages'])
    run(local_docs, ['git', 'checkout', 'master'])
    return local_docs
