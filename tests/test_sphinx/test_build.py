"""Test function."""

import pytest

from sphinxcontrib.versioning.sphinx_ import build
from sphinxcontrib.versioning.versions import Versions


@pytest.mark.parametrize('no_feature', [True, False])
def test_simple(tmpdir, local_docs, no_feature):
    """Verify versions are included in HTML.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param bool no_feature: Don't include feature branch in versions. Makes sure there are no false positives.
    """
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1)] + ([] if no_feature else [('', 'feature', 'heads', 2)]))

    result = build(str(local_docs), str(target), versions, 'master', list())
    assert result == 0

    contents = target.join('contents.html').read()
    assert '<a href=".">master</a></li>' in contents
    if no_feature:
        assert '<li><a href=".">feature</a></li>' not in contents
    else:
        assert '<li><a href=".">feature</a></li>' in contents


@pytest.mark.parametrize('project', [True, False, True, False])
def test_isolation(tmpdir, local_docs, project):
    """Make sure Sphinx doesn't alter global state and carry over settings between builds.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param bool project: Set project in conf.py, else set copyright.
    """
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1)])

    overflow = ['-D', 'project=Robpol86' if project else 'copyright="2016, SCV"']
    result = build(str(local_docs), str(target), versions, 'master', overflow)
    assert result == 0

    contents = target.join('contents.html').read()
    if project:
        assert 'Robpol86' in contents
        assert '2016, SCV' not in contents
    else:
        assert 'Robpol86' not in contents
        assert '2016, SCV' in contents


def test_overflow(tmpdir, local_docs):
    """Test sphinx-build overflow feature.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    """
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1)])

    result = build(str(local_docs), str(target), versions, 'master', ['-D', 'copyright=2016, SCV'])
    assert result == 0

    contents = target.join('contents.html').read()
    assert '2016, SCV' in contents


def test_sphinx_error(tmpdir, local_docs):
    """Test error handling.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    """
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1)])

    local_docs.join('conf.py').write('undefined')

    result = build(str(local_docs), str(target), versions, 'master', list())
    assert result == 1


def test_custom_sidebar(tmpdir, local_docs):
    """Make sure user's sidebar item is kept intact.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    """
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1)])

    local_docs.join('conf.py').write(
        'templates_path = ["_templates"]\n'
        'html_sidebars = {"**": ["localtoc.html", "custom.html"]}\n'
    )
    local_docs.ensure('_templates', 'custom.html').write('<h3>Custom Sidebar</h3><ul><li>Test</li></ul>')

    result = build(str(local_docs), str(target), versions, 'master', list())
    assert result == 0

    contents = target.join('contents.html').read()
    assert '<li><a href=".">master</a></li>' in contents
    assert '<h3>Custom Sidebar</h3>' in contents


def test_subdirs(tmpdir, local_docs):
    """Make sure relative URLs in `versions` works with RST files in subdirectories.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    """
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1), ('', 'feature', 'heads', 2)])
    versions['feature']['url'] = 'feature'

    for i in range(1, 6):
        path = ['subdir'] * i + ['sub.rst']
        local_docs.join('contents.rst').write('    ' + '/'.join(path)[:-4] + '\n', mode='a')
        local_docs.ensure(*path).write(
            '.. _sub:\n'
            '\n'
            'Sub\n'
            '===\n'
            '\n'
            'Sub directory sub page documentation.\n'
        )

    result = build(str(local_docs), str(target), versions, 'master', list())
    assert result == 0

    contents = target.join('contents.html').read()
    assert '<li><a href=".">master</a></li>' in contents
    assert '<li><a href="feature">feature</a></li>' in contents

    page = target.join('subdir', 'sub.html').read()
    assert '<li><a href="..">master</a></li>' in page
    assert '<li><a href="../feature">feature</a></li>' in page
    page = target.join('subdir', 'subdir', 'sub.html').read()
    assert '<li><a href="../..">master</a></li>' in page
    assert '<li><a href="../../feature">feature</a></li>' in page
    page = target.join('subdir', 'subdir', 'subdir', 'sub.html').read()
    assert '<li><a href="../../..">master</a></li>' in page
    assert '<li><a href="../../../feature">feature</a></li>' in page
    page = target.join('subdir', 'subdir', 'subdir', 'subdir', 'sub.html').read()
    assert '<li><a href="../../../..">master</a></li>' in page
    assert '<li><a href="../../../../feature">feature</a></li>' in page
    page = target.join('subdir', 'subdir', 'subdir', 'subdir', 'subdir', 'sub.html').read()
    assert '<li><a href="../../../../..">master</a></li>' in page
    assert '<li><a href="../../../../../feature">feature</a></li>' in page
