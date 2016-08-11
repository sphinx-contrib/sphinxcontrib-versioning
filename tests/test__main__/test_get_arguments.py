"""Test function in module."""

import pytest

from sphinxcontrib.versioning.__main__ import __doc__ as doc, get_arguments


def test_overflow():
    """Test get_arguments() overflow to sphinx-build."""
    config = get_arguments([__file__, 'build', 'html', 'docs'], doc)
    assert config.overflow == tuple()

    config = get_arguments([__file__, 'build', 'html', 'docs', '--'], doc)
    assert config.overflow == tuple()

    config = get_arguments([__file__, 'build', 'html', 'docs', '--', '-D', 'setting=value'], doc)
    assert config.overflow == ('-D', 'setting=value')


@pytest.mark.parametrize('mode', ['default', 'cli', 'cli2'])
def test_string(mode):
    """Test get_arguments() with string arguments.

    :param str mode: Scenario to test for.
    """
    argv = [__file__, 'push', 'gh-pages', 'html', 'docs']
    expected = {'--root-ref': 'master', 'REL_SOURCE': ['docs'], '--grm-exclude': list()}
    if mode.startswith('cli'):
        argv.extend(['-r', 'feature', '-e', '.gitignore'])
        expected['--root-ref'] = 'feature'
        expected['--grm-exclude'].append('.gitignore')
        if mode.endswith('2'):
            argv.extend(['-e', 'docs/README.md', 'two'])
            expected['--grm-exclude'].append('docs/README.md')
            expected['REL_SOURCE'].append('two')

    config = get_arguments(argv, doc)
    assert config.grm_exclude == expected['--grm-exclude']
    assert config.root_ref == expected['--root-ref']
    assert config.build is False
    assert config.rel_source == expected['REL_SOURCE']


def test_line_length(capsys):
    """Make sure {program} substitute doesn't make --help too wide.

    :param capsys: pytest fixture.
    """
    with pytest.raises(SystemExit):
        get_arguments([__file__, '--help'], doc)
    stdout = capsys.readouterr()[0]
    for line in stdout.splitlines():
        assert len(line) <= 80
