"""Test function in module."""

import pytest

from sphinxcontrib.versioning.__main__ import __doc__ as doc, get_arguments

ARGV = (__file__, 'build', 'docs', 'html')


def test_overflow():
    """Test get_arguments() overflow to sphinx-build."""
    config = get_arguments(ARGV, doc)
    assert config['overflow'] == list()

    config = get_arguments(ARGV + ('--',), doc)
    assert config['overflow'] == tuple()

    config = get_arguments(ARGV + ('--', '-D', 'setting=value'), doc)
    assert config['overflow'] == ('-D', 'setting=value')


@pytest.mark.parametrize('mode', ['default', 'cli', 'cli2'])
def test_string(mode):
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


def test_line_length(capsys):
    """Make sure {program} substitute doesn't make --help too wide.

    :param capsys: pytest fixture.
    """
    with pytest.raises(SystemExit):
        get_arguments([__file__, '--help'], doc)
    stdout = capsys.readouterr()[0]
    for line in stdout.splitlines():
        assert len(line) <= 80
