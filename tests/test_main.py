"""Test functions in __main__.py."""

import pytest

from sphinxcontrib.versioning.__main__ import __doc__ as doc, get_arguments

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
    expected = {'--file': 'conf.py', '--root-ref': 'master', '--additional-src': list()}
    if mode.startswith('cli'):
        argv += ['-f', 'index.rst', '-r', 'feature', '-s', 'one']
        expected = {'--file': 'index.rst', '--root-ref': 'feature', '--additional-src': ['one']}
        if mode.endswith('2'):
            argv.extend(['-s', 'two'])
            expected['--additional-src'].append('two')

    config = get_arguments(argv, doc)
    assert config['--file'] == expected['--file']
    assert config['--root-ref'] == expected['--root-ref']
    assert config['--additional-src'] == expected['--additional-src']
