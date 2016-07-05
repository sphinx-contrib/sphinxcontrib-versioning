"""Test compatibility with Sphinx themes."""

import difflib

import pytest

from sphinxcontrib.versioning.sphinx_ import build
from sphinxcontrib.versioning.versions import Versions


@pytest.mark.parametrize('theme', [
    'alabaster',
    'sphinx_rtd_theme',
])
def test(tmpdir, theme, run):
    """Test with different themes. Verify not much changed between sphinx-build and sphinx-versioning.

    :param tmpdir: pytest fixture.
    :param str theme: Theme name to use.
    :param run: conftest fixture.
    """
    source = tmpdir.ensure_dir('source')
    target_n = tmpdir.ensure_dir('target_n')
    target_y = tmpdir.ensure_dir('target_y')
    versions = Versions([
        ('', 'master', 'heads', 1),
        ('', 'feature', 'heads', 2),
        ('', 'v1.0.0', 'tags', 3),
        ('', 'v1.2.0', 'tags', 4),
        ('', 'v2.0.0', 'tags', 5),
        ('', 'v2.1.0', 'tags', 6),
        ('', 'v2.2.0', 'tags', 7),
        ('', 'v2.3.0', 'tags', 8),
        ('', 'v2.4.0', 'tags', 9),
        ('', 'v2.5.0', 'tags', 10),
        ('', 'v2.6.0', 'tags', 11),
        ('', 'v2.7.0', 'tags', 12),
        ('', 'testing_branch', 'heads', 13),
    ], sort='semver')

    source.join('conf.py').write('html_theme="{}"'.format(theme))
    source.join('contents.rst').write('Test\n====\n\nSample documentation.')

    # Build with normal sphinx-build.
    run(source, ['sphinx-build', '.', str(target_n)])
    contents_n = target_n.join('contents.html').read()
    assert 'master' not in contents_n

    # Build with versions.
    result = build(str(source), str(target_y), versions, 'master', list())
    assert result == 0
    contents_y = target_y.join('contents.html').read()
    assert 'master' in contents_y

    # Verify nothing removed.
    diff = list(difflib.unified_diff(contents_n.splitlines(True), contents_y.splitlines(True)))[2:]
    assert diff
    for line in diff:
        assert not line.startswith('-')
