"""Test compatibility with Sphinx themes."""

import difflib

import pytest

from sphinxcontrib.versioning.sphinx_ import build
from sphinxcontrib.versioning.versions import Versions

THEMES = [
    'alabaster',
    'sphinx_rtd_theme',
    'classic',
    'sphinxdoc',
    'traditional',
    'nature',
    'pyramid',
    'bizstyle',
]


@pytest.mark.parametrize('theme', THEMES)
def test_supported(tmpdir, config, local_docs, run, theme):
    """Test with different themes. Verify not much changed between sphinx-build and sphinx-versioning.

    :param tmpdir: pytest fixture.
    :param sphinxcontrib.versioning.lib.Config config: conftest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param str theme: Theme name to use.
    """
    config.overflow = ('-D', 'html_theme=' + theme)
    target_n = tmpdir.ensure_dir('target_n')
    target_y = tmpdir.ensure_dir('target_y')
    versions = Versions([
        ('', 'master', 'heads', 1, 'conf.py'),
        ('', 'feature', 'heads', 2, 'conf.py'),
        ('', 'v1.0.0', 'tags', 3, 'conf.py'),
        ('', 'v1.2.0', 'tags', 4, 'conf.py'),
        ('', 'v2.0.0', 'tags', 5, 'conf.py'),
        ('', 'v2.1.0', 'tags', 6, 'conf.py'),
        ('', 'v2.2.0', 'tags', 7, 'conf.py'),
        ('', 'v2.3.0', 'tags', 8, 'conf.py'),
        ('', 'v2.4.0', 'tags', 9, 'conf.py'),
        ('', 'v2.5.0', 'tags', 10, 'conf.py'),
        ('', 'v2.6.0', 'tags', 11, 'conf.py'),
        ('', 'v2.7.0', 'tags', 12, 'conf.py'),
        ('', 'testing_branch', 'heads', 13, 'conf.py'),
    ], sort=['semver'])

    # Build with normal sphinx-build.
    run(local_docs, ['sphinx-build', '.', str(target_n), '-D', 'html_theme=' + theme])
    contents_n = target_n.join('contents.html').read()
    assert 'master' not in contents_n

    # Build with versions.
    build(str(local_docs), str(target_y), versions, 'master', True)
    contents_y = target_y.join('contents.html').read()
    assert 'master' in contents_y

    # Verify nothing removed.
    diff = list(difflib.unified_diff(contents_n.splitlines(True), contents_y.splitlines(True)))[2:]
    assert diff
    for line in diff:
        assert not line.startswith('-')

    # Verify added.
    for name in (r['name'] for r in versions.remotes):
        assert any(name in line for line in diff if line.startswith('+'))


def test_sphinx_rtd_theme(tmpdir, config, local_docs):
    """Test sphinx_rtd_theme features.

    :param tmpdir: pytest fixture.
    :param config: conftest fixture.
    :param local_docs: conftest fixture.
    """
    local_docs.join('conf.py').write('html_theme="sphinx_rtd_theme"')

    # Build branches only.
    target_b = tmpdir.ensure_dir('target_b')
    versions = Versions([('', 'master', 'heads', 1, 'conf.py'), ('', 'feature', 'heads', 2, 'conf.py')], ['semver'])
    build(str(local_docs), str(target_b), versions, 'master', True)
    contents = target_b.join('contents.html').read()
    assert '<dt>Branches</dt>' in contents
    assert '<dt>Tags</dt>' not in contents

    # Build tags only.
    target_t = tmpdir.ensure_dir('target_t')
    versions = Versions([('', 'v1.0.0', 'tags', 3, 'conf.py'), ('', 'v1.2.0', 'tags', 4, 'conf.py')], sort=['semver'])
    config.root_ref = config.banner_main_ref = 'v1.2.0'
    build(str(local_docs), str(target_t), versions, 'v1.2.0', True)
    contents = target_t.join('contents.html').read()
    assert '<dt>Branches</dt>' not in contents
    assert '<dt>Tags</dt>' in contents

    # Build both.
    target_bt = tmpdir.ensure_dir('target_bt')
    versions = Versions([
        ('', 'master', 'heads', 1, 'conf.py'), ('', 'feature', 'heads', 2, 'conf.py'),
        ('', 'v1.0.0', 'tags', 3, 'conf.py'), ('', 'v1.2.0', 'tags', 4, 'conf.py')
    ], sort=['semver'])
    config.root_ref = 'master'
    build(str(local_docs), str(target_bt), versions, 'master', True)
    contents = target_bt.join('contents.html').read()
    assert '<dt>Branches</dt>' in contents
    assert '<dt>Tags</dt>' in contents


@pytest.mark.parametrize('theme', THEMES)
def test_banner(tmpdir, banner, config, local_docs, theme):
    """Test banner messages.

    :param tmpdir: pytest fixture.
    :param banner: conftest fixture.
    :param sphinxcontrib.versioning.lib.Config config: conftest fixture.
    :param local_docs: conftest fixture.
    :param str theme: Theme name to use.
    """
    config.overflow = ('-D', 'html_theme=' + theme)
    config.show_banner = True
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1, 'conf.py'), ('', 'feature', 'heads', 2, 'conf.py')])
    versions['master']['found_docs'] = ('contents',)
    versions['feature']['found_docs'] = ('contents',)

    build(str(local_docs), str(target), versions, 'feature', False)

    banner(target.join('contents.html'), '../master/contents.html',
           'the development version of Python. The main version is master')
