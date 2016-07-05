"""Test function."""

import pytest

from sphinxcontrib.versioning.sphinx_ import build
from sphinxcontrib.versioning.versions import Versions


@pytest.mark.parametrize('no_feature', [True, False])
def test_simple(tmpdir, no_feature):
    """Verify versions are included in HTML.

    :param tmpdir: pytest fixture.
    :param bool no_feature: Don't include feature branch in versions. Makes sure there are no false positives.
    """
    source = tmpdir.ensure_dir('source')
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1)] + ([] if no_feature else [('', 'feature', 'heads', 2)]))

    source.ensure('conf.py')
    source.join('contents.rst').write('Test\n====\n\nSample documentation.')

    result = build(str(source), str(target), versions, 'master', list())
    assert result == 0

    contents = target.join('contents.html').read()
    assert '<a href=".">master</a></li>' in contents
    if no_feature:
        assert '<a href=".">feature</a></li>' not in contents
    else:
        assert '<a href=".">feature</a></li>' in contents


@pytest.mark.parametrize('project', [True, False, True, False])
def test_isolation(tmpdir, project):
    """Make sure Sphinx doesn't alter global state and carry over settings between builds.

    :param tmpdir: pytest fixture.
    :param bool project: Set project in conf.py, else set copyright.
    """
    source = tmpdir.ensure_dir('source')
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1)])

    source.join('conf.py').write('project = "Robpol86"' if project else 'copyright = "2016, SCV"')
    source.join('contents.rst').write('Test\n====\n\nSample documentation.')

    result = build(str(source), str(target), versions, 'master', list())
    assert result == 0

    contents = target.join('contents.html').read()
    if project:
        assert 'Robpol86' in contents
        assert '2016, SCV' not in contents
    else:
        assert 'Robpol86' not in contents
        assert '2016, SCV' in contents


def test_overflow(tmpdir):
    """Test sphinx-build overflow feature.

    :param tmpdir: pytest fixture.
    """
    source = tmpdir.ensure_dir('source')
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1)])

    source.ensure('conf.py')
    source.join('contents.rst').write('Test\n====\n\nSample documentation.')

    result = build(str(source), str(target), versions, 'master', ['-D', 'copyright=2016, SCV'])
    assert result == 0

    contents = target.join('contents.html').read()
    assert '2016, SCV' in contents


def test_sphinx_error(tmpdir):
    """Test error handling.

    :param tmpdir: pytest fixture.
    """
    source = tmpdir.ensure_dir('source')
    target = tmpdir.ensure_dir('target')
    versions = Versions([('', 'master', 'heads', 1)])

    source.join('conf.py').write('undefined')
    source.join('contents.rst').write('Test\n====\n\nSample documentation.')

    result = build(str(source), str(target), versions, 'master', list())
    assert result == 1
