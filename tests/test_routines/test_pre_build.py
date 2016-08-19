"""Test function in module."""

import posixpath

import py
import pytest

from sphinxcontrib.versioning.lib import HandledError
from sphinxcontrib.versioning.routines import gather_git_info, pre_build
from sphinxcontrib.versioning.versions import Versions


def test_single(local_docs):
    """With single version.

    :param local_docs: conftest fixture.
    """
    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))
    versions.set_root_remote('master')
    assert len(versions) == 1

    # Run and verify directory.
    exported_root = py.path.local(pre_build(str(local_docs), versions, tuple()))
    assert len(exported_root.listdir()) == 1
    assert exported_root.join(versions['master']['sha'], 'conf.py').read() == ''

    # Verify root_dir and master_doc..
    expected = ['contents']
    assert sorted(posixpath.join(r['root_dir'], r['master_doc']) for r in versions.remotes) == expected


def test_dual(local_docs, run):
    """With two versions, one with master_doc defined.

    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    run(local_docs, ['git', 'checkout', 'feature'])
    local_docs.join('conf.py').write('master_doc = "index"\n')
    local_docs.join('index.rst').write(
        'Test\n'
        '====\n'
        '\n'
        'Sample documentation.\n'
    )
    run(local_docs, ['git', 'add', 'conf.py', 'index.rst'])
    run(local_docs, ['git', 'commit', '-m', 'Adding docs with master_doc'])
    run(local_docs, ['git', 'push', 'origin', 'feature'])

    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))
    versions.set_root_remote('master')
    assert len(versions) == 2

    # Run and verify directory.
    exported_root = py.path.local(pre_build(str(local_docs), versions, tuple()))
    assert len(exported_root.listdir()) == 2
    assert exported_root.join(versions['master']['sha'], 'conf.py').read() == ''
    assert exported_root.join(versions['feature']['sha'], 'conf.py').read() == 'master_doc = "index"\n'

    # Verify versions root_dirs and master_docs.
    expected = ['contents', 'feature/index']
    assert sorted(posixpath.join(r['root_dir'], r['master_doc']) for r in versions.remotes) == expected


def test_file_collision(local_docs, run):
    """Test handling of filename collisions between generates files from root ref and branch names.

    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    run(local_docs, ['git', 'checkout', '-b', '_static'])
    run(local_docs, ['git', 'push', 'origin', '_static'])

    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))
    versions.set_root_remote('master')
    assert len(versions) == 2

    # Verify versions root_dirs and master_docs.
    pre_build(str(local_docs), versions, tuple())
    expected = ['_static_/contents', 'contents']
    assert sorted(posixpath.join(r['root_dir'], r['master_doc']) for r in versions.remotes) == expected


def test_invalid_name(local_docs, run):
    """Test handling of branch names with invalid root_dir characters.

    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    run(local_docs, ['git', 'checkout', '-b', 'robpol86/feature'])
    run(local_docs, ['git', 'push', 'origin', 'robpol86/feature'])

    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))
    versions.set_root_remote('master')
    assert len(versions) == 2

    # Verify versions root_dirs and master_docs.
    pre_build(str(local_docs), versions, tuple())
    expected = ['contents', 'robpol86_feature/contents']
    assert sorted(posixpath.join(r['root_dir'], r['master_doc']) for r in versions.remotes) == expected


def test_error(local_docs, run):
    """Test with a bad root ref. Also test skipping bad non-root refs.

    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    run(local_docs, ['git', 'checkout', '-b', 'a_good', 'master'])
    run(local_docs, ['git', 'checkout', '-b', 'c_good', 'master'])
    run(local_docs, ['git', 'checkout', '-b', 'b_broken', 'master'])
    local_docs.join('conf.py').write('master_doc = exception\n')
    run(local_docs, ['git', 'commit', '-am', 'Broken version.'])
    run(local_docs, ['git', 'checkout', '-b', 'd_broken', 'b_broken'])
    run(local_docs, ['git', 'push', 'origin', 'a_good', 'b_broken', 'c_good', 'd_broken'])

    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()), sort=['alpha'])
    assert [r['name'] for r in versions.remotes] == ['a_good', 'b_broken', 'c_good', 'd_broken', 'master']

    # Bad root ref.
    versions.set_root_remote('b_broken')
    with pytest.raises(HandledError):
        pre_build(str(local_docs), versions, tuple())

    # Remove bad non-root refs.
    versions.set_root_remote('master')
    pre_build(str(local_docs), versions, tuple())
    assert [r['name'] for r in versions.remotes] == ['a_good', 'c_good', 'master']
