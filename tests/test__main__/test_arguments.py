"""Test mixing sources of arguments/settings."""

from os.path import join

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
@pytest.mark.parametrize('source_cli', [False, True])
@pytest.mark.parametrize('source_conf', [False, True])
def test_overflow(local_empty, push, source_cli, source_conf):
    """Test -- overflow to sphinx-build.

    :param local_empty: conftest fixture.
    :param bool push: Run push sub command instead of build.
    :param bool source_cli: Set value from command line arguments.
    :param bool source_conf: Set value from conf.py file.
    """
    if push:
        args = ['push', 'docs', 'gh-pages', '.']
    else:
        args = ['build', 'docs', join('docs', '_build', 'html')]

    # Setup source(s).
    if source_cli:
        args += ['--', '-D', 'setting=value']
    if source_conf:
        local_empty.ensure('docs', 'contents.rst')
        local_empty.ensure('docs', 'conf.py').write('scv_overflow = ("-D", "key=value")')

    # Run.
    result = CliRunner().invoke(cli, args)
    config = result.exception.args[0]

    # Verify.
    if source_cli:
        assert config.overflow == ('-D', 'setting=value')
    elif source_conf:
        assert config.overflow == ('-D', 'key=value')
    else:
        assert config.overflow == tuple()


@pytest.mark.parametrize('push', [False, True])
def test_args(push):
    """Test positional arguments.

    :param bool push: Run push sub command instead of build.
    """
    # Single rel_source.
    if push:
        result = CliRunner().invoke(cli, ['push', 'docs', 'gh-pages', '.'])
        rel_source, dest_branch, rel_dest = result.exception.args[1:]
        assert dest_branch == 'gh-pages'
        assert rel_dest == '.'
    else:
        result = CliRunner().invoke(cli, ['build', 'docs', join('docs', '_build', 'html')])
        rel_source, destination = result.exception.args[1:]
        assert destination == join('docs', '_build', 'html')
    assert rel_source == ('docs',)

    # Multiple rel_source.
    if push:
        result = CliRunner().invoke(cli, ['push', 'docs', 'docs2', 'documentation', 'dox', 'feature', 'html'])
        rel_source, dest_branch, rel_dest = result.exception.args[1:]
        assert dest_branch == 'feature'
        assert rel_dest == 'html'
    else:
        result = CliRunner().invoke(cli, ['build', 'docs', 'docs2', 'documentation', 'dox', 'html'])
        rel_source, destination = result.exception.args[1:]
        assert destination == 'html'
    assert rel_source == ('docs', 'docs2', 'documentation', 'dox')


@pytest.mark.parametrize('push', [False, True])
def test_global_options(monkeypatch, tmpdir, caplog, local_empty, run, push):
    """Test options that apply to all sub commands.

    :param monkeypatch: pytest fixture.
    :param tmpdir: pytest fixture.
    :param caplog: pytest extension fixture.
    :param local_empty: conftest fixture.
    :param run: conftest fixture.
    :param bool push: Run push sub command instead of build.
    """
    if push:
        args = ['push', 'docs', 'gh-pages', '.']
    else:
        args = ['build', 'docs', join('docs', '_build', 'html')]

    # Defaults.
    result = CliRunner().invoke(cli, args)
    config = result.exception.args[0]
    assert config.chdir == str(local_empty)
    assert config.git_root == str(local_empty)
    assert config.local_conf is None
    assert config.no_colors is False
    assert config.no_local_conf is False
    assert config.verbose == 0

    # Defined.
    empty = tmpdir.ensure_dir('empty')
    repo = tmpdir.ensure_dir('repo')
    run(repo, ['git', 'init'])
    local_empty.ensure('conf.py')
    args = ['-L', '-l', 'conf.py', '-c', str(empty), '-g', str(repo), '-N', '-v', '-v'] + args
    result = CliRunner().invoke(cli, args)
    config = result.exception.args[0]
    assert config.chdir == str(empty)
    assert config.git_root == str(repo)
    assert config.local_conf is None  # Overridden by -L.
    assert config.no_colors is True
    assert config.no_local_conf is True
    assert config.verbose == 2

    # Set in conf.py. They'll be ignored.
    monkeypatch.chdir(local_empty)
    local_empty.ensure('docs', 'contents.rst')
    local_empty.ensure('docs', 'conf.py').write(
        'scv_chdir = ".."\n'
        'scv_git_root = ".."\n'
        'scv_no_colors = False\n'
        'scv_verbose = 1\n'
    )
    args = args[7:]  # Remove -L -l -c and -g.
    result = CliRunner().invoke(cli, args)
    records = [(r.levelname, r.message) for r in caplog.records]
    config = result.exception.args[0]
    assert config.chdir == str(local_empty)
    assert config.git_root == str(local_empty)
    assert config.local_conf == join('docs', 'conf.py')
    assert config.no_colors is True
    assert config.no_local_conf is False
    assert config.verbose == 2
    assert ('DEBUG', 'chdir already set in config, skipping.') in records
    assert ('DEBUG', 'git_root already set in config, skipping.') in records
    assert ('DEBUG', 'no_colors already set in config, skipping.') in records
    assert ('DEBUG', 'verbose already set in config, skipping.') in records


@pytest.mark.parametrize('mode', ['bad filename', 'rel_source', 'override'])
@pytest.mark.parametrize('no_local_conf', [False, True])
@pytest.mark.parametrize('push', [False, True])
def test_global_options_local_conf(caplog, local_empty, mode, no_local_conf, push):
    """Test detection of local conf.py file.

    :param caplog: pytest extension fixture.
    :param local_empty: conftest fixture.
    :param str mode: Scenario to test for.
    :param no_local_conf: Toggle -L.
    :param bool push: Run push sub command instead of build.
    """
    args = ['-L'] if no_local_conf else []
    if push:
        args += ['push', 'docs', 'gh-pages', '.']
    else:
        args += ['build', 'docs', join('docs', '_build', 'html')]

    # Run.
    if mode == 'bad filename':
        local_empty.ensure('docs', 'config.py')
        args = ['-l', join('docs', 'config.py')] + args
    elif mode == 'rel_source':
        local_empty.ensure('docs', 'conf.py')
    else:
        local_empty.ensure('other', 'conf.py')
        args = ['-l', join('other', 'conf.py')] + args
    result = CliRunner().invoke(cli, args)
    config = result.exception.args[0]
    records = [(r.levelname, r.message) for r in caplog.records]

    # Verify.
    if no_local_conf:
        assert config.local_conf is None
        assert config.no_local_conf is True
        return
    if mode == 'bad filename':
        assert config == 1  # SystemExit.
        assert records[-2] == ('ERROR', 'Path "{}" must end with conf.py.'.format(join('docs', 'config.py')))
    elif mode == 'rel_source':
        assert config.local_conf == join('docs', 'conf.py')
        assert config.no_local_conf is False
    else:
        assert config.local_conf == join('other', 'conf.py')
        assert config.no_local_conf is False


@pytest.mark.parametrize('push', [False, True])
@pytest.mark.parametrize('source_cli', [False, True])
@pytest.mark.parametrize('source_conf', [False, True])
def test_sub_command_options(local_empty, push, source_cli, source_conf):
    """Test non-global options that apply to all sub commands.

    :param local_empty: conftest fixture.
    :param bool push: Run push sub command instead of build.
    :param bool source_cli: Set value from command line arguments.
    :param bool source_conf: Set value from conf.py file.
    """
    if push:
        args = ['push', 'docs', 'gh-pages', '.']
    else:
        args = ['build', 'docs', join('docs', '_build', 'html')]

    # Setup source(s).
    if source_cli:
        args += ['-itT', '-p', 'branches', '-r', 'feature', '-s', 'semver', '-w', 'master', '-W', '[0-9]']
        args += ['-aAb', '-B', 'x']
        if push:
            args += ['-e' 'README.md', '-P', 'rem']
    if source_conf:
        local_empty.ensure('docs', 'contents.rst')
        local_empty.ensure('docs', 'conf.py').write(
            'import re\n\n'
            'scv_banner_greatest_tag = True\n'
            'scv_banner_main_ref = "y"\n'
            'scv_banner_recent_tag = True\n'
            'scv_greatest_tag = True\n'
            'scv_invert = True\n'
            'scv_priority = "tags"\n'
            'scv_push_remote = "origin2"\n'
            'scv_recent_tag = True\n'
            'scv_root_ref = "other"\n'
            'scv_show_banner = True\n'
            'scv_sort = ("alpha",)\n'
            'scv_whitelist_branches = ("other",)\n'
            'scv_whitelist_tags = re.compile("^[0-9]$")\n'
            'scv_grm_exclude = ("README.rst",)\n'
        )

    # Run.
    result = CliRunner().invoke(cli, args)
    config = result.exception.args[0]

    # Verify.
    if source_cli:
        assert config.banner_greatest_tag is True
        assert config.banner_main_ref == 'x'
        assert config.banner_recent_tag is True
        assert config.greatest_tag is True
        assert config.invert is True
        assert config.priority == 'branches'
        assert config.recent_tag is True
        assert config.root_ref == 'feature'
        assert config.show_banner is True
        assert config.sort == ('semver',)
        assert config.whitelist_branches == ('master',)
        assert config.whitelist_tags == ('[0-9]',)
        if push:
            assert config.grm_exclude == ('README.md',)
            assert config.push_remote == 'rem'
    elif source_conf:
        assert config.banner_greatest_tag is True
        assert config.banner_main_ref == 'y'
        assert config.banner_recent_tag is True
        assert config.greatest_tag is True
        assert config.invert is True
        assert config.priority == 'tags'
        assert config.recent_tag is True
        assert config.root_ref == 'other'
        assert config.show_banner is True
        assert config.sort == ('alpha',)
        assert config.whitelist_branches == ('other',)
        assert config.whitelist_tags.pattern == '^[0-9]$'
        if push:
            assert config.grm_exclude == ('README.rst',)
            assert config.push_remote == 'origin2'
    else:
        assert config.banner_greatest_tag is False
        assert config.banner_main_ref == 'master'
        assert config.banner_recent_tag is False
        assert config.greatest_tag is False
        assert config.invert is False
        assert config.priority is None
        assert config.recent_tag is False
        assert config.root_ref == 'master'
        assert config.show_banner is False
        assert config.sort == tuple()
        assert config.whitelist_branches == tuple()
        assert config.whitelist_tags == tuple()
        if push:
            assert config.grm_exclude == tuple()
            assert config.push_remote == 'origin'


@pytest.mark.parametrize('push', [False, True])
def test_sub_command_options_other(push):
    """Test additional option values for all sub commands.

    :param bool push: Run push sub command instead of build.
    """
    if push:
        args = ['push', 'docs', 'gh-pages', '.']
    else:
        args = ['build', 'docs', join('docs', '_build', 'html')]

    # Defined.
    args += ['-p', 'tags', '-s', 'semver', '-s', 'time']
    if push:
        args += ['-e' 'one', '-e', 'two', '-e', 'three', '-e', 'four']
    result = CliRunner().invoke(cli, args)
    config = result.exception.args[0]
    assert config.priority == 'tags'
    assert config.sort == ('semver', 'time')
    if push:
        assert config.grm_exclude == ('one', 'two', 'three', 'four')
