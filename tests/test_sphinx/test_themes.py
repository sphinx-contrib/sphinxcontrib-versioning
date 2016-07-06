"""Test compatibility with Sphinx themes."""

import difflib

import pytest

from sphinxcontrib.versioning.sphinx_ import build
from sphinxcontrib.versioning.versions import Versions


@pytest.mark.parametrize('theme', [
    'alabaster',
    'sphinx_rtd_theme',
    'classic',
    'sphinxdoc',
])
def test_supported(tmpdir, run, theme):
    """Test with different themes. Verify not much changed between sphinx-build and sphinx-versioning.

    :param tmpdir: pytest fixture.
    :param run: conftest fixture.
    :param str theme: Theme name to use.
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
    ], sort=['semver'])

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

    # Verify added.
    for name, _ in versions:
        assert any(name in line for line in diff if line.startswith('+'))


def test_sphinx_rtd_theme(tmpdir):
    """Test sphinx_rtd_theme features.

    :param tmpdir: pytest fixture.
    """
    source = tmpdir.ensure_dir('source')
    source.join('conf.py').write('html_theme="sphinx_rtd_theme"')
    source.join('contents.rst').write('Test\n====\n\nSample documentation.')

    # Build branches only.
    target_b = tmpdir.ensure_dir('target_b')
    versions = Versions([('', 'master', 'heads', 1), ('', 'feature', 'heads', 2)], sort=['semver'])
    result = build(str(source), str(target_b), versions, 'master', list())
    assert result == 0
    contents = target_b.join('contents.html').read()
    assert '<dt>Branches</dt>' in contents
    assert '<dt>Tags</dt>' not in contents

    # Build tags only.
    target_t = tmpdir.ensure_dir('target_t')
    versions = Versions([('', 'v1.0.0', 'tags', 3), ('', 'v1.2.0', 'tags', 4)], sort=['semver'])
    result = build(str(source), str(target_t), versions, 'v1.2.0', list())
    assert result == 0
    contents = target_t.join('contents.html').read()
    assert '<dt>Branches</dt>' not in contents
    assert '<dt>Tags</dt>' in contents

    # Build both.
    target_bt = tmpdir.ensure_dir('target_bt')
    versions = Versions([
        ('', 'master', 'heads', 1), ('', 'feature', 'heads', 2),
        ('', 'v1.0.0', 'tags', 3), ('', 'v1.2.0', 'tags', 4)
    ], sort=['semver'])
    result = build(str(source), str(target_bt), versions, 'master', list())
    assert result == 0
    contents = target_bt.join('contents.html').read()
    assert '<dt>Branches</dt>' in contents
    assert '<dt>Tags</dt>' in contents
