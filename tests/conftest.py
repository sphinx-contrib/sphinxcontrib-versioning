"""pytest fixtures for this directory."""

import re

import pytest

from sphinxcontrib.versioning.git import run_command
from sphinxcontrib.versioning.lib import Config

RE_BANNER = re.compile('>(?:<a href="([^"]+)">)?<b>Warning:</b> This document is for ([^<]+).(?:</a>)?</p>')
RE_URLS = re.compile('<li><a href="[^"]+">[^<]+</a></li>')


def run(directory, command, *args, **kwargs):
    """Run command using run_command() function. Supports string and py.path paths.

    :param directory: Root git directory and current working directory.
    :param iter command: Command to run.
    :param iter args: Passed to run_command().
    :param dict kwargs: Passed to run_command().

    :return: run_command() output.
    :rtype: str
    """
    return run_command(str(directory), [str(i) for i in command], *args, **kwargs)


def pytest_namespace():
    """Add objects to the pytest namespace. Can be retrieved by importing pytest and accessing pytest.<name>.

    :return: Namespace dict.
    :rtype: dict
    """
    return dict(
        run=run,
    )


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
def banner():
    """Verify banner in HTML file match expected."""
    def match(path, expected_url=None, expected_base=None):
        """Assert equals and return file contents.

        :param py.path.local path: Path to file to read.
        :param str expected_url: Expected URL in <a href="" /> link.
        :param str expected_base: Expected base message.

        :return: File contents.
        :rtype: str
        """
        contents = path.read()
        actual = RE_BANNER.findall(contents)
        if not expected_url and not expected_base:
            assert not actual
        else:
            assert actual == [(expected_url, expected_base)]
        return contents
    return match


@pytest.fixture
def urls():
    """Verify URLs in HTML file match expected."""
    def match(path, expected):
        """Assert equals and return file contents.

        :param py.path.local path: Path to file to read.
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
def local_empty(tmpdir):
    """Local git repository with no commits.

    :param tmpdir: pytest fixture.

    :return: Path to repo root.
    :rtype: py.path
    """
    repo = tmpdir.ensure_dir('local')
    run(repo, ['git', 'init'])
    return repo


@pytest.fixture
def remote(tmpdir):
    """Remote git repository with nothing pushed to it.

    :param tmpdir: pytest fixture.

    :return: Path to bare repo root.
    :rtype: py.path
    """
    repo = tmpdir.ensure_dir('remote')
    run(repo, ['git', 'init', '--bare'])
    return repo


@pytest.fixture
def local_commit(local_empty):
    """Local git repository with one commit.

    :param local_empty: local fixture.

    :return: Path to repo root.
    :rtype: py.path
    """
    local_empty.join('README').write('Dummy readme file.')
    run(local_empty, ['git', 'add', 'README'])
    run(local_empty, ['git', 'commit', '-m', 'Initial commit.'])
    return local_empty


@pytest.fixture
def local(local_commit, remote):
    """Local git repository with branches, light tags, and annotated tags pushed to remote.

    :param local_commit: local fixture.
    :param remote: local fixture.

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
def local_light(tmpdir, local, remote):
    """Light-weight local repository similar to how Travis/AppVeyor clone repos.

    :param tmpdir: pytest fixture.
    :param local: local fixture.
    :param remote: local fixture.

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
def outdate_local(tmpdir, local_light, remote):
    """Clone remote to other directory and push changes. Causes `local` fixture to be outdated.

    :param tmpdir: pytest fixture.
    :param local_light: local fixture.
    :param remote: local fixture.

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
def local_docs(local):
    """Local repository with Sphinx doc files. Pushed to remote.

    :param local: local fixture.

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
def local_docs_ghp(local_docs):
    """Add an orphaned branch to remote.

    :param local_docs: local fixture.
    """
    run(local_docs, ['git', 'checkout', '--orphan', 'gh-pages'])
    run(local_docs, ['git', 'rm', '-rf', '.'])
    local_docs.join('README').write('Orphaned branch for HTML docs.')
    run(local_docs, ['git', 'add', 'README'])
    run(local_docs, ['git', 'commit', '-m', 'Initial Commit'])
    run(local_docs, ['git', 'push', 'origin', 'gh-pages'])
    run(local_docs, ['git', 'checkout', 'master'])
    return local_docs
