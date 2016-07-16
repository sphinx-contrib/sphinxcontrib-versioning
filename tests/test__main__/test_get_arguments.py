"""Test function in module."""

import pytest

from sphinxcontrib.versioning.__main__ import __doc__ as doc, get_arguments


def test_overflow():
    """Test get_arguments() overflow to sphinx-build."""
    config = get_arguments([__file__, 'build', 'html', 'docs'], doc)
    assert config['overflow'] == list()

    config = get_arguments([__file__, 'build', 'html', 'docs', '--'], doc)
    assert config['overflow'] == list()

    config = get_arguments([__file__, 'build', 'html', 'docs', '--', '-D', 'setting=value'], doc)
    assert config['overflow'] == ['-D', 'setting=value']


@pytest.mark.parametrize('mode', ['default', 'cli', 'cli2'])
def test_string(mode):
    """Test get_arguments() with string arguments.

    :param str mode: Scenario to test for.
    """
    argv = [__file__, 'build', 'html', 'docs']
    expected = {'--root-ref': 'master', 'REL_SOURCE': ['docs']}
    if mode.startswith('cli'):
        argv += ['-r', 'feature']
        expected['--root-ref'] = 'feature'
        if mode.endswith('2'):
            argv.extend(['two'])
            expected['REL_SOURCE'].append('two')

    config = get_arguments(argv, doc)
    assert config['--root-ref'] == expected['--root-ref']
    assert config['REL_SOURCE'] == expected['REL_SOURCE']


def test_line_length(capsys):
    """Make sure {program} substitute doesn't make --help too wide.

    :param capsys: pytest fixture.
    """
    with pytest.raises(SystemExit):
        get_arguments([__file__, '--help'], doc)
    stdout = capsys.readouterr()[0]
    for line in stdout.splitlines():
        assert len(line) <= 80
