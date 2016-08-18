"""Test function in module."""

import pytest

from sphinxcontrib.versioning.git import export
from sphinxcontrib.versioning.lib import HandledError
from sphinxcontrib.versioning.routines import build_all, gather_git_info
from sphinxcontrib.versioning.versions import Versions


def test_single(tmpdir, local_docs):
    """With single version.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    """
    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))
    versions['master']['url'] = 'contents.html'
    versions.set_root_remote('master')

    # Export.
    exported_root = tmpdir.ensure_dir('exported_root')
    export(str(local_docs), versions['master']['sha'], str(exported_root.join(versions['master']['sha'])))

    # Run and verify directory.
    destination = tmpdir.ensure_dir('destination')
    build_all(str(exported_root), str(destination), versions, tuple())
    actual = sorted(f.relto(destination) for f in destination.visit() if f.check(dir=True))
    expected = [
        '.doctrees',
        '_sources',
        '_static',
    ]
    assert actual == expected

    # Verify HTML links.
    contents = destination.join('contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents


@pytest.mark.parametrize('parallel', [False, True])
@pytest.mark.parametrize('triple', [False, True])
def test_multiple(tmpdir, local_docs, run, triple, parallel):
    """With two or three versions.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param bool triple: With three versions (including master) instead of two.
    :param bool parallel: Run sphinx-build with -j option.
    """
    run(local_docs, ['git', 'tag', 'v1.0.0'])
    run(local_docs, ['git', 'push', 'origin', 'v1.0.0'])
    if triple:
        run(local_docs, ['git', 'tag', 'v1.0.1'])
        run(local_docs, ['git', 'push', 'origin', 'v1.0.1'])

    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))
    versions['master']['url'] = 'contents.html'
    versions['v1.0.0']['url'] = 'v1.0.0/contents.html'
    if triple:
        versions['v1.0.1']['url'] = 'v1.0.1/contents.html'
    versions.set_root_remote('master')

    # Export (git tags point to same master sha).
    exported_root = tmpdir.ensure_dir('exported_root')
    export(str(local_docs), versions['master']['sha'], str(exported_root.join(versions['master']['sha'])))

    # Run and verify directory.
    destination = tmpdir.ensure_dir('destination')
    build_all(str(exported_root), str(destination), versions, ('-j', '2') if parallel else tuple())
    actual = sorted(f.relto(destination) for f in destination.visit() if f.check(dir=True))
    expected = [
        '.doctrees',
        '_sources',
        '_static',
        'v1.0.0',
        'v1.0.0/.doctrees',
        'v1.0.0/_sources',
        'v1.0.0/_static',
    ]
    if triple:
        expected.extend([
            'v1.0.1',
            'v1.0.1/.doctrees',
            'v1.0.1/_sources',
            'v1.0.1/_static',
        ])
    assert actual == expected

    # Verify root ref HTML links.
    contents = destination.join('contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents
    assert '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>' in contents
    if triple:
        assert '<li><a href="v1.0.1/contents.html">v1.0.1</a></li>' in contents

    # Verify v1.0.0 links.
    contents = destination.join('v1.0.0/contents.html').read()
    assert '<li><a href="../contents.html">master</a></li>' in contents
    assert '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>' in contents
    if triple:
        assert '<li><a href="../v1.0.1/contents.html">v1.0.1</a></li>' in contents
    else:
        return

    # Verify v1.0.1 links.
    contents = destination.join('v1.0.1/contents.html').read()
    assert '<li><a href="../contents.html">master</a></li>' in contents
    assert '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>' in contents
    assert '<li><a href="../v1.0.1/contents.html">v1.0.1</a></li>' in contents


@pytest.mark.parametrize('parallel', [False, True])
def test_error(tmpdir, local_docs, run, parallel):
    """Test with a bad root ref. Also test skipping bad non-root refs.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param bool parallel: Run sphinx-build with -j option.
    """
    run(local_docs, ['git', 'checkout', '-b', 'a_good', 'master'])
    run(local_docs, ['git', 'checkout', '-b', 'c_good', 'master'])
    run(local_docs, ['git', 'checkout', '-b', 'b_broken', 'master'])
    local_docs.join('conf.py').write('master_doc = exception\n')
    run(local_docs, ['git', 'commit', '-am', 'Broken version.'])
    run(local_docs, ['git', 'checkout', '-b', 'd_broken', 'b_broken'])
    run(local_docs, ['git', 'push', 'origin', 'a_good', 'b_broken', 'c_good', 'd_broken'])

    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))
    versions['master']['url'] = 'contents.html'
    versions['a_good']['url'] = 'a_good/contents.html'
    versions['c_good']['url'] = 'c_good/contents.html'
    versions['b_broken']['url'] = 'b_broken/contents.html'
    versions['d_broken']['url'] = 'd_broken/contents.html'

    exported_root = tmpdir.ensure_dir('exported_root')
    export(str(local_docs), versions['master']['sha'], str(exported_root.join(versions['master']['sha'])))
    export(str(local_docs), versions['b_broken']['sha'], str(exported_root.join(versions['b_broken']['sha'])))

    overflow = ('-j', '2') if parallel else tuple()

    # Bad root ref.
    versions.set_root_remote('b_broken')
    destination = tmpdir.ensure_dir('destination')
    with pytest.raises(HandledError):
        build_all(str(exported_root), str(destination), versions, overflow)

    # Remove bad non-root refs.
    versions.set_root_remote('master')
    build_all(str(exported_root), str(destination), versions, overflow)
    assert [r[0] for r in versions] == ['a_good', 'c_good', 'master']

    # Verify root ref HTML links.
    contents = destination.join('contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents
    assert '<li><a href="a_good/contents.html">a_good</a></li>' in contents
    assert '<li><a href="c_good/contents.html">c_good</a></li>' in contents
    assert 'b_broken' not in contents
    assert 'd_broken' not in contents

    # Verify a_good links.
    contents = destination.join('a_good/contents.html').read()
    assert '<li><a href="../contents.html">master</a></li>' in contents
    assert '<li><a href="../a_good/contents.html">a_good</a></li>' in contents
    assert '<li><a href="../c_good/contents.html">c_good</a></li>' in contents
    assert 'b_broken' not in contents
    assert 'd_broken' not in contents

    # Verify c_good links.
    contents = destination.join('c_good/contents.html').read()
    assert '<li><a href="../contents.html">master</a></li>' in contents
    assert '<li><a href="../a_good/contents.html">a_good</a></li>' in contents
    assert '<li><a href="../c_good/contents.html">c_good</a></li>' in contents
    assert 'b_broken' not in contents
    assert 'd_broken' not in contents


def test_all_errors(tmpdir, local_docs, run):
    """Test good root ref with all bad non-root refs.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    run(local_docs, ['git', 'checkout', '-b', 'a_broken', 'master'])
    local_docs.join('conf.py').write('master_doc = exception\n')
    run(local_docs, ['git', 'commit', '-am', 'Broken version.'])
    run(local_docs, ['git', 'checkout', '-b', 'b_broken', 'a_broken'])
    run(local_docs, ['git', 'push', 'origin', 'a_broken', 'b_broken'])

    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))
    versions['master']['url'] = 'contents.html'
    versions['a_broken']['url'] = 'a_broken/contents.html'
    versions['b_broken']['url'] = 'b_broken/contents.html'
    versions.set_root_remote('master')

    exported_root = tmpdir.ensure_dir('exported_root')
    export(str(local_docs), versions['master']['sha'], str(exported_root.join(versions['master']['sha'])))
    export(str(local_docs), versions['b_broken']['sha'], str(exported_root.join(versions['b_broken']['sha'])))

    # Run.
    destination = tmpdir.ensure_dir('destination')
    build_all(str(exported_root), str(destination), versions, tuple())
    assert [r[0] for r in versions] == ['master']

    # Verify root ref HTML links.
    contents = destination.join('contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents
    assert 'a_broken' not in contents
    assert 'b_broken' not in contents
