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
        assert '<a href=".">feature</a></li>' not in contents
    else:
        assert '<a href=".">feature</a></li>' in contents


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
    assert '<a href=".">master</a></li>' in contents
    assert '<h3>Custom Sidebar</h3>' in contents
