"""Test objects in module."""

import pytest

from sphinxcontrib.versioning.__main__ import __doc__ as doc, get_arguments, main

ARGV = (__file__, 'build', 'docs', 'html')


def test_get_arguments_overflow():
    """Test get_arguments() overflow to sphinx-build."""
    config = get_arguments(ARGV, doc)
    assert config['overflow'] == list()

    config = get_arguments(ARGV + ('--',), doc)
    assert config['overflow'] == tuple()

    config = get_arguments(ARGV + ('--', '-D', 'setting=value'), doc)
    assert config['overflow'] == ('-D', 'setting=value')


@pytest.mark.parametrize('mode', ['default', 'cli', 'cli2'])
def test_get_arguments_string(mode):
    """Test get_arguments() with string arguments.

    :param str mode: Scenario to test for.
    """
    argv = list(ARGV)
    expected = {'--root-ref': 'master', '--additional-src': list()}
    if mode.startswith('cli'):
        argv += ['-r', 'feature', '-s', 'one']
        expected = {'--root-ref': 'feature', '--additional-src': ['one']}
        if mode.endswith('2'):
            argv.extend(['-s', 'two'])
            expected['--additional-src'].append('two')

    config = get_arguments(argv, doc)
    assert config['--root-ref'] == expected['--root-ref']
    assert config['--additional-src'] == expected['--additional-src']


def test_main_working(monkeypatch, tmpdir, local_docs, run):
    """Test main() with working docs.

    :param monkeypatch: pytest fixture.
    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    monkeypatch.chdir(local_docs)
    local_docs.ensure('subdir', 'sub.rst').write(
        '.. _sub:\n'
        '\n'
        'Sub\n'
        '===\n'
        '\n'
        'Sub directory sub page documentation.\n'
    )
    local_docs.join('contents.rst').write('    subdir/sub\n', mode='a')
    run(local_docs, ['git', 'add', 'subdir', 'contents.rst'])
    run(local_docs, ['git', 'commit', '-m', 'Adding subdir docs.'])
    run(local_docs, ['git', 'tag', 'v1.0.0'])
    run(local_docs, ['git', 'push', 'origin', 'master', 'v1.0.0'])

    destination = tmpdir.ensure_dir('destination')
    config = get_arguments([__file__, 'build', '.', str(destination)], doc)
    main(config)

    # Check master.
    contents = destination.join('contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents
    assert '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>' in contents
    contents = destination.join('subdir', 'sub.html').read()
    assert '<li><a href="../contents.html">master</a></li>' in contents
    assert '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>' in contents

    # Check v1.0.0.
    contents = destination.join('v1.0.0', 'contents.html').read()
    assert '<li><a href="../contents.html">master</a></li>' in contents
    assert '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>' in contents
    contents = destination.join('v1.0.0', 'subdir', 'sub.html').read()
    assert '<li><a href="../../contents.html">master</a></li>' in contents
    assert '<li><a href="../../v1.0.0/contents.html">v1.0.0</a></li>' in contents
