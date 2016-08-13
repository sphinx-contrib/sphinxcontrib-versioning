"""Test function in module."""

import pytest
from click.testing import CliRunner

from sphinxcontrib.versioning.__main__ import cli


@pytest.fixture(autouse=True)
def setup(monkeypatch, local_empty):
    """Set __main__.NO_EXECUTE to True before every test in this module and sets CWD to an empty git repo.

    :param monkeypatch: pytest fixture.
    :param local_empty: conftest fixture.
    """
    monkeypatch.setattr('sphinxcontrib.versioning.__main__.NO_EXECUTE', True)
    monkeypatch.chdir(local_empty)


@pytest.mark.parametrize('push', [False, True])
def test_overflow(push):
    """Test -- overflow to sphinx-build.

    :param bool push: Run push sub command instead of build.
    """
    if push:
        args = ['push', 'gh-pages', '.', 'docs']
    else:
        args = ['build', 'docs/_build/html', 'docs']

    result = CliRunner().invoke(cli, args)
    config = result.exception.args[0]
    assert config.overflow == tuple()

    result = CliRunner().invoke(cli, args + ['--'])
    config = result.exception.args[0]
    assert config.overflow == tuple()

    result = CliRunner().invoke(cli, args + ['--', '-D', 'setting=value'])
    config = result.exception.args[0]
    assert config.overflow == ('-D', 'setting=value')


@pytest.mark.parametrize('push', [False, True])
def test_args(push):
    """Test positional arguments.

    :param bool push: Run push sub command instead of build.
    """
    # Single rel_source.
    if push:
        result = CliRunner().invoke(cli, ['push', 'gh-pages', '.', 'docs'])
        rel_source, dest_branch, rel_dest = result.exception.args[1:]
        assert dest_branch == 'gh-pages'
        assert rel_dest == '.'
    else:
        result = CliRunner().invoke(cli, ['build', 'docs/_build/html', 'docs'])
        rel_source, destination = result.exception.args[1:]
        assert destination == 'docs/_build/html'
    assert rel_source == ('docs',)

    # Multiple rel_source.
    if push:
        result = CliRunner().invoke(cli, ['push', 'feature', 'html', 'docs', 'docs2', 'documentation', 'dox'])
        rel_source, dest_branch, rel_dest = result.exception.args[1:]
        assert dest_branch == 'feature'
        assert rel_dest == 'html'
    else:
        result = CliRunner().invoke(cli, ['build', 'html', 'docs', 'docs2', 'documentation', 'dox'])
        rel_source, destination = result.exception.args[1:]
        assert destination == 'html'
    assert rel_source == ('docs', 'docs2', 'documentation', 'dox')


@pytest.mark.parametrize('push', [False, True])
def test_global_options(tmpdir, local_empty, run, push):
    """Test options that apply to all sub commands.

    :param tmpdir: pytest fixture.
    :param local_empty: conftest fixture.
    :param run: conftest fixture.
    :param bool push: Run push sub command instead of build.
    """
    if push:
        args = ['push', 'gh-pages', '.', 'docs']
    else:
        args = ['build', 'docs/_build/html', 'docs']

    # Defaults.
    result = CliRunner().invoke(cli, args)
    config = result.exception.args[0]
    assert config.chdir == str(local_empty)
    assert config.no_colors is False
    assert config.git_root == str(local_empty)
    assert config.verbose is False

    # Defined.
    empty = tmpdir.ensure_dir('empty')
    repo = tmpdir.ensure_dir('repo')
    run(repo, ['git', 'init'])
    args = ['-c', str(empty), '-C', '-g', str(repo), '-v'] + args
    result = CliRunner().invoke(cli, args)
    config = result.exception.args[0]
    assert config.chdir == str(empty)
    assert config.no_colors is True
    assert config.git_root == str(repo)
    assert config.verbose is True


@pytest.mark.parametrize('push', [False, True])
def test_sub_command_options(push):
    """Test non-global options that apply to all sub commands.

    :param bool push: Run push sub command instead of build.
    """
    if push:
        args = ['push', 'gh-pages', '.', 'docs']
    else:
        args = ['build', 'docs/_build/html', 'docs']

    # Defaults
    result = CliRunner().invoke(cli, args)
    config = result.exception.args[0]
    assert config.invert is False
    assert config.priority is None
    assert config.root_ref == 'master'
    assert config.sort == tuple()
    assert config.greatest_tag is False
    assert config.recent_tag is False
    if push:
        assert config.grm_exclude == tuple()

    # Defined.
    args = args[:1] + ['-itT', '-p', 'branches', '-r', 'feature', '-s', 'semver'] + args[1:]
    if push:
        args = args[:1] + ['-e' 'README.md'] + args[1:]
    result = CliRunner().invoke(cli, args)
    config = result.exception.args[0]
    assert config.invert is True
    assert config.priority == 'branches'
    assert config.root_ref == 'feature'
    assert config.sort == ('semver',)
    assert config.greatest_tag is True
    assert config.recent_tag is True
    if push:
        assert config.grm_exclude == ('README.md',)


@pytest.mark.parametrize('push', [False, True])
def test_sub_command_options_other(push):
    """Test additional option values for all sub commands.

    :param bool push: Run push sub command instead of build.
    """
    if push:
        args = ['push', 'gh-pages', '.', 'docs']
    else:
        args = ['build', 'docs/_build/html', 'docs']

    # Defined.
    args = args[:1] + ['-p', 'tags', '-s', 'semver', '-s', 'time'] + args[1:]
    if push:
        args = args[:1] + ['-e' 'one', '-e', 'two', '-e', 'three', '-e', 'four'] + args[1:]
    result = CliRunner().invoke(cli, args)
    config = result.exception.args[0]
    assert config.priority == 'tags'
    assert config.sort == ('semver', 'time')
    if push:
        assert config.grm_exclude == ('one', 'two', 'three', 'four')
