"""Test function in module."""

from os.path import join
from subprocess import CalledProcessError

import pytest

from sphinxcontrib.versioning.git import clone, GitError, IS_WINDOWS


def test_no_exclude(tmpdir, local_docs):
    """Simple test without "git rm".

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    """
    new_root = tmpdir.ensure_dir('new_root')
    clone(str(local_docs), str(new_root), 'origin', 'master', '', None)
    assert new_root.join('conf.py').check(file=True)
    assert new_root.join('contents.rst').check(file=True)
    assert new_root.join('README').check(file=True)
    branch = pytest.run(new_root, ['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
    assert branch == 'master'
    pytest.run(local_docs, ['git', 'diff-index', '--quiet', 'HEAD', '--'])  # Exit 0 if nothing changed.
    pytest.run(new_root, ['git', 'diff-index', '--quiet', 'HEAD', '--'])  # Exit 0 if nothing changed.


def test_exclude(tmpdir, local):
    """Test with "git rm".

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    """
    pytest.run(local, ['git', 'checkout', 'feature'])
    local.join('one.txt').write('one')
    local.join('two.txt').write('two')
    local.ensure('sub', 'three.txt').write('three')
    local.ensure('sub', 'four.txt').write('four')
    pytest.run(local, ['git', 'add', 'one.txt', 'two.txt', 'sub'])
    pytest.run(local, ['git', 'commit', '-m', 'Adding new files.'])
    pytest.run(local, ['git', 'push', 'origin', 'feature'])
    pytest.run(local, ['git', 'checkout', 'master'])

    # Run.
    exclude = [
        '.travis.yml', 'appveyor.yml',  # Ignored (nonexistent), show warnings.
        'README', 'two.txt', join('sub', 'four.txt'),  # Only leave these.
    ]
    new_root = tmpdir.ensure_dir('new_root')
    clone(str(local), str(new_root), 'origin', 'feature', '.', exclude)

    # Verify files.
    assert new_root.join('.git').check(dir=True)
    assert new_root.join('README').check(file=True)
    assert new_root.join('sub', 'four.txt').read() == 'four'
    assert new_root.join('two.txt').read() == 'two'
    paths = sorted(f.relto(new_root) for f in new_root.visit() if new_root.join('.git') not in f.parts())
    assert paths == ['README', 'sub', join('sub', 'four.txt'), 'two.txt']

    # Verify original repo state.
    pytest.run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])  # Verify unchanged.
    branch = pytest.run(local, ['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
    assert branch == 'master'

    # Verify new repo state.
    with pytest.raises(CalledProcessError):
        pytest.run(new_root, ['git', 'diff-index', '--quiet', 'HEAD', '--'])
    branch = pytest.run(new_root, ['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
    assert branch == 'feature'
    status = pytest.run(new_root, ['git', 'status', '--porcelain'])
    assert status == 'D  one.txt\nD  sub/three.txt\n'


def test_exclude_subdir(tmpdir, local):
    """Test with grm_dir set to a subdirectory.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    """
    local.ensure('sub', 'three.txt').write('three')
    local.ensure('sub', 'four.txt').write('four')
    pytest.run(local, ['git', 'add', 'sub'])
    pytest.run(local, ['git', 'commit', '-m', 'Adding new files.'])
    pytest.run(local, ['git', 'push', 'origin', 'master'])

    new_root = tmpdir.ensure_dir('new_root')
    clone(str(local), str(new_root), 'origin', 'master', 'sub', ['three.txt'])
    paths = sorted(f.relto(new_root) for f in new_root.visit() if new_root.join('.git') not in f.parts())
    assert paths == ['README', 'sub', join('sub', 'three.txt')]

    status = pytest.run(new_root, ['git', 'status', '--porcelain'])
    assert status == 'D  sub/four.txt\n'


def test_exclude_patterns(tmpdir, local):
    """Test with grm_dir set to a subdirectory.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    """
    local.join('one.md').write('one')
    local.join('two.txt').write('two')
    local.ensure('sub', 'three.txt').write('three')
    local.ensure('sub', 'four.md').write('four')
    local.ensure('sub', 'five.md').write('five')
    local.join('six.md').write('two')
    pytest.run(local, ['git', 'add', 'sub', 'one.md', 'two.txt', 'six.md'])
    pytest.run(local, ['git', 'commit', '-m', 'Adding new files.'])
    pytest.run(local, ['git', 'push', 'origin', 'master'])

    new_root = tmpdir.ensure_dir('new_root')
    clone(str(local), str(new_root), 'origin', 'master', '.', ['*.md', join('*', '*.md')])
    paths = sorted(f.relto(new_root) for f in new_root.visit() if new_root.join('.git') not in f.parts())
    assert paths == ['one.md', 'six.md', 'sub', join('sub', 'five.md'), join('sub', 'four.md')]

    status = pytest.run(new_root, ['git', 'status', '--porcelain'])
    assert status == 'D  README\nD  sub/three.txt\nD  two.txt\n'


def test_bad_branch_rel_dest_exclude(tmpdir, local):
    """Test bad data.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    """
    # Unknown branch.
    with pytest.raises(GitError) as exc:
        clone(str(local), str(tmpdir.ensure_dir('new_root')), 'origin', 'unknown_branch', '.', None)
    assert 'Remote branch unknown_branch not found in upstream origin' in exc.value.output

    # Not a branch.
    with pytest.raises(GitError) as exc:
        clone(str(local), str(tmpdir.ensure_dir('new_root')), 'origin', 'light_tag', '.', None)
    assert 'fatal: ref HEAD is not a symbolic ref' in exc.value.output

    # rel_dest outside of repo.
    with pytest.raises(GitError) as exc:
        clone(str(local), str(tmpdir.ensure_dir('new_root2')), 'origin', 'master', '..', ['README'])
    assert "'..' is outside repository" in exc.value.output

    # rel_dest invalid.
    with pytest.raises(GitError) as exc:
        clone(str(local), str(tmpdir.ensure_dir('new_root3')), 'origin', 'master', 'unknown', ['README'])
    assert "pathspec 'unknown' did not match any files" in exc.value.output

    # No origin.
    pytest.run(local, ['git', 'remote', 'rename', 'origin', 'origin2'])
    with pytest.raises(GitError) as exc:
        clone(str(local), str(tmpdir.ensure_dir('new_root3')), 'origin', 'master', '.', None)
    assert 'Git repo missing remote "origin".' in exc.value.message
    assert 'origin2\t' in exc.value.output
    assert 'origin\t' not in exc.value.output

    # No remote.
    pytest.run(local, ['git', 'remote', 'rm', 'origin2'])
    with pytest.raises(GitError) as exc:
        clone(str(local), str(tmpdir.ensure_dir('new_root3')), 'origin', 'master', '.', None)
    assert 'Git repo has no remotes.' in exc.value.message
    assert not exc.value.output

    # Bad remote.
    pytest.run(local, ['git', 'remote', 'add', 'origin', local.join('does_not_exist')])
    with pytest.raises(GitError) as exc:
        clone(str(local), str(tmpdir.ensure_dir('new_root4')), 'origin', 'master', '.', None)
    if IS_WINDOWS:
        assert "'{}' does not appear to be a git repository".format(local.join('does_not_exist')) in exc.value.output
    else:
        assert "repository '{}' does not exist".format(local.join('does_not_exist')) in exc.value.output


def test_multiple_remotes(tmpdir, local, remote):
    """Test multiple remote URLs being carried over.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param remote: conftest fixture.
    """
    origin_push = tmpdir.ensure_dir('origin_push')
    pytest.run(origin_push, ['git', 'init', '--bare'])
    pytest.run(local, ['git', 'remote', 'set-url', '--push', 'origin', str(origin_push)])
    origin2_fetch = tmpdir.ensure_dir('origin2_fetch')
    pytest.run(origin2_fetch, ['git', 'init', '--bare'])
    pytest.run(local, ['git', 'remote', 'add', 'origin2', str(origin2_fetch)])
    origin2_push = tmpdir.ensure_dir('origin2_push')
    pytest.run(origin2_push, ['git', 'init', '--bare'])
    pytest.run(local, ['git', 'remote', 'set-url', '--push', 'origin2', str(origin2_push)])

    new_root = tmpdir.ensure_dir('new_root')
    clone(str(local), str(new_root), 'origin', 'master', '', None)

    output = pytest.run(new_root, ['git', 'remote', '-v'])
    actual = output.strip().splitlines()
    expected = [
        'origin\t{} (fetch)'.format(remote),
        'origin\t{} (push)'.format(origin_push),
        'origin2\t{} (fetch)'.format(origin2_fetch),
        'origin2\t{} (push)'.format(origin2_push),
    ]
    assert actual == expected
