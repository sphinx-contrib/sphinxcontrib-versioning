"""Test function."""

import pytest

from sphinxcontrib.versioning.lib import HandledError
from sphinxcontrib.versioning.sphinx_ import build
from sphinxcontrib.versioning.versions import Versions


@pytest.mark.parametrize('no_feature', [True, False])
def test_simple(tmpdir, local_docs, urls, no_feature):
    """Verify versions are included in HTML.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param urls: conftest fixture.
    :param bool no_feature: Don't include feature branch in versions. Makes sure there are no false positives.
    """
    target = tmpdir.ensure_dir('target')
    versions = Versions(
        [('', 'master', 'heads', 1, 'conf.py')] + ([] if no_feature else [('', 'feature', 'heads', 2, 'conf.py')])
    )

    build(str(local_docs), str(target), versions, 'master', True)

    expected = ['<li><a href="master/contents.html">master</a></li>']
    if not no_feature:
        expected.append('<li><a href="feature/contents.html">feature</a></li>')
    urls(target.join('contents.html'), expected)


@pytest.mark.parametrize('project', [True, False, True, False])
def test_isolation(tmpdir, config, local_docs, project):
    """Make sure Sphinx doesn't alter global state and carry over settings between builds.

    :param tmpdir: pytest fixture.
    :param sphinxcontrib.versioning.lib.Config config: conftest fixture.
    :param local_docs: conftest fixture.
    :param bool project: Set project in conf.py, else set copyright.
    """
    config.overflow = ('-D', 'project=Robpol86' if project else 'copyright="2016, SCV"')
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1, 'conf.py')])

    build(str(local_docs), str(target), versions, 'master', True)

    contents = target.join('contents.html').read()
    if project:
        assert 'Robpol86' in contents
        assert '2016, SCV' not in contents
    else:
        assert 'Robpol86' not in contents
        assert '2016, SCV' in contents


def test_overflow(tmpdir, config, local_docs):
    """Test sphinx-build overflow feature.

    :param tmpdir: pytest fixture.
    :param sphinxcontrib.versioning.lib.Config config: conftest fixture.
    :param local_docs: conftest fixture.
    """
    config.overflow = ('-D', 'copyright=2016, SCV')
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1, 'conf.py')])

    build(str(local_docs), str(target), versions, 'master', True)

    contents = target.join('contents.html').read()
    assert '2016, SCV' in contents


def test_sphinx_error(tmpdir, local_docs):
    """Test error handling.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    """
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1, 'conf.py')])

    local_docs.join('conf.py').write('undefined')

    with pytest.raises(HandledError):
        build(str(local_docs), str(target), versions, 'master', True)


@pytest.mark.parametrize('pre_existing_versions', [False, True])
def test_custom_sidebar(tmpdir, local_docs, urls, pre_existing_versions):
    """Make sure user's sidebar item is kept intact.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param urls: conftest fixture.
    :param bool pre_existing_versions: Test if user already has versions.html in conf.py.
    """
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1, 'conf.py')])

    if pre_existing_versions:
        local_docs.join('conf.py').write(
            'templates_path = ["_templates"]\n'
            'html_sidebars = {"**": ["versions.html", "localtoc.html", "custom.html"]}\n'
        )
    else:
        local_docs.join('conf.py').write(
            'templates_path = ["_templates"]\n'
            'html_sidebars = {"**": ["localtoc.html", "custom.html"]}\n'
        )
    local_docs.ensure('_templates', 'custom.html').write('<h3>Custom Sidebar</h3><ul><li>Test</li></ul>')

    build(str(local_docs), str(target), versions, 'master', True)

    contents = urls(target.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    assert '<h3>Custom Sidebar</h3>' in contents


def test_versions_override(tmpdir, local_docs):
    """Verify GitHub/BitBucket versions are overridden.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    """
    versions = Versions([('', 'master', 'heads', 1, 'conf.py'), ('', 'feature', 'heads', 2, 'conf.py')])

    local_docs.join('conf.py').write(
        'templates_path = ["_templates"]\n'
        'html_sidebars = {"**": ["custom.html"]}\n'
        'html_context = dict(github_version="replace_me", bitbucket_version="replace_me")\n'
    )
    local_docs.ensure('_templates', 'custom.html').write(
        '<h3>Custom Sidebar</h3>\n'
        '<ul>\n'
        '<li>GitHub: {{ github_version }}</li>\n'
        '<li>BitBucket: {{ bitbucket_version }}</li>\n'
        '</ul>\n'
    )

    target = tmpdir.ensure_dir('target_master')
    build(str(local_docs), str(target), versions, 'master', True)
    contents = target.join('contents.html').read()
    assert '<li>GitHub: master</li>' in contents
    assert '<li>BitBucket: master</li>' in contents

    target = tmpdir.ensure_dir('target_feature')
    build(str(local_docs), str(target), versions, 'feature', False)
    contents = target.join('contents.html').read()
    assert '<li>GitHub: feature</li>' in contents
    assert '<li>BitBucket: feature</li>' in contents


def test_layout_override(tmpdir, local_docs):
    """Verify users can still override layout.html.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    """
    versions = Versions([('', 'master', 'heads', 1, 'conf.py')])

    local_docs.join('conf.py').write(
        'templates_path = ["_templates"]\n'
    )
    local_docs.ensure('_templates', 'layout.html').write(
        '{% extends "!layout.html" %}\n'
        '{% block extrahead %}\n'
        '<!-- Hidden Message -->\n'
        '{% endblock %}\n'
    )

    target = tmpdir.ensure_dir('target_master')
    build(str(local_docs), str(target), versions, 'master', True)
    contents = target.join('contents.html').read()
    assert '<!-- Hidden Message -->' in contents


def test_subdirs(tmpdir, local_docs, urls):
    """Make sure relative URLs in `versions` works with RST files in subdirectories.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param urls: conftest fixture.
    """
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1, 'conf.py'), ('', 'feature', 'heads', 2, 'conf.py')])
    versions['master']['found_docs'] = ('contents',)
    versions['feature']['found_docs'] = ('contents',)

    for i in range(1, 6):
        path = ['subdir'] * i + ['sub.rst']
        versions['master']['found_docs'] += ('/'.join(path)[:-4],)
        versions['feature']['found_docs'] += ('/'.join(path)[:-4],)
        local_docs.join('contents.rst').write('    ' + '/'.join(path)[:-4] + '\n', mode='a')
        local_docs.ensure(*path).write(
            '.. _sub:\n'
            '\n'
            'Sub\n'
            '===\n'
            '\n'
            'Sub directory sub page documentation.\n'
        )

    build(str(local_docs), str(target), versions, 'master', True)

    urls(target.join('contents.html'), [
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="feature/contents.html">feature</a></li>'
    ])
    for i in range(1, 6):
        urls(target.join(*['subdir'] * i + ['sub.html']), [
            '<li><a href="{}master/{}sub.html">master</a></li>'.format('../' * i, 'subdir/' * i),
            '<li><a href="{}feature/{}sub.html">feature</a></li>'.format('../' * i, 'subdir/' * i),
        ])


def test_import_setup(tmpdir, local_docs, urls):
    """Test handling of conf.py files that import from setup.py.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param urls: conftest fixture.
    """
    versions = Versions([('', 'master', 'heads', 1, 'conf.py')])

    local_docs.join('setup.py').write('PROJECT_NAME = "myProject"\n')
    local_docs.join('conf.py').write(
        'from setup import PROJECT_NAME\n'
        'assert PROJECT_NAME == "myProject"\n'
    )

    target = tmpdir.ensure_dir('target')
    build(str(local_docs), str(target), versions, 'master', True)

    expected = ['<li><a href="master/contents.html">master</a></li>']
    urls(target.join('contents.html'), expected)
