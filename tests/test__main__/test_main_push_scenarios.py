"""Test calls to main() with different command line options."""

import os
import re
from subprocess import CalledProcessError, PIPE, Popen, STDOUT

import py
import pytest


def test_no_exclude(local_docs_ghp, urls):
    """Test with successful push to remote. Don't remove/exclude any files.

    :param local_docs_ghp: conftest fixture.
    :param urls: conftest fixture.
    """
    # Run.
    output = pytest.run(local_docs_ghp, ['sphinx-versioning', 'push', '.', 'gh-pages', '.'])
    assert 'Traceback' not in output
    assert 'Failed to push to remote repository.' not in output

    # Check HTML.
    pytest.run(local_docs_ghp, ['git', 'checkout', 'gh-pages'])
    pytest.run(local_docs_ghp, ['git', 'pull', 'origin', 'gh-pages'])
    urls(local_docs_ghp.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(local_docs_ghp.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])

    # Run again.
    output = pytest.run(local_docs_ghp, ['sphinx-versioning', 'push', '.', 'gh-pages', '.'])
    assert 'Traceback' not in output
    assert 'Failed to push to remote repository.' not in output
    assert 'No significant changes to commit.' in output

    # Check SHAs.
    old_sha = pytest.run(local_docs_ghp, ['git', 'rev-parse', 'HEAD']).strip()
    pytest.run(local_docs_ghp, ['git', 'pull', 'origin', 'gh-pages'])
    sha = pytest.run(local_docs_ghp, ['git', 'rev-parse', 'HEAD']).strip()
    assert sha == old_sha


def test_exclude(local_docs_ghp, urls):
    """Test excluding files and REL_DEST. Also test changing files.

    :param local_docs_ghp: conftest fixture.
    :param urls: conftest fixture.
    """
    pytest.run(local_docs_ghp, ['git', 'checkout', 'gh-pages'])
    local_docs_ghp.ensure('documents', 'delete.txt').write('a')
    local_docs_ghp.ensure('documents', 'keep.txt').write('b')
    pytest.run(local_docs_ghp, ['git', 'add', 'documents'])
    pytest.run(local_docs_ghp, ['git', 'commit', '-m', 'Adding files.'])
    pytest.run(local_docs_ghp, ['git', 'push', 'origin', 'gh-pages'])

    # Run.
    output = pytest.run(local_docs_ghp, ['sphinx-versioning', 'push', '.', 'gh-pages', 'documents', '-e', 'keep.txt'])
    assert 'Traceback' not in output

    # Check files.
    pytest.run(local_docs_ghp, ['git', 'pull', 'origin', 'gh-pages'])
    destination = local_docs_ghp.join('documents')
    urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])
    assert not destination.join('delete.txt').check()
    assert destination.join('keep.txt').check()

    # Change and commit.
    pytest.run(local_docs_ghp, ['git', 'checkout', 'master'])
    local_docs_ghp.join('contents.rst').write('\nNew Unexpected Line!\n', mode='a')
    pytest.run(local_docs_ghp, ['git', 'commit', '-am', 'Changing docs.'])
    pytest.run(local_docs_ghp, ['git', 'push', 'origin', 'master'])

    # Run.
    output = pytest.run(local_docs_ghp, ['sphinx-versioning', 'push', '.', 'gh-pages', 'documents', '-e', 'keep.txt'])
    assert 'Traceback' not in output

    # Check files.
    pytest.run(local_docs_ghp, ['git', 'checkout', 'gh-pages'])
    pytest.run(local_docs_ghp, ['git', 'pull', 'origin', 'gh-pages'])
    contents = list()
    contents.append(urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>']))
    contents.append(urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>']))
    assert 'New Unexpected Line!' in contents[0]
    assert 'New Unexpected Line!' in contents[1]
    assert not destination.join('delete.txt').check()
    assert destination.join('keep.txt').check()


def test_root_ref(local_docs_ghp):
    """Test passing root_ref value from push Click command to build Click command.

    :param local_docs_ghp: conftest fixture.
    """
    pytest.run(local_docs_ghp, ['git', 'tag', 'v1.0.0'])
    pytest.run(local_docs_ghp, ['git', 'push', 'origin', 'v1.0.0'])

    # Run.
    output = pytest.run(local_docs_ghp, ['sphinx-versioning', '-N', 'push', '-t', '.', 'gh-pages', '.'])
    assert 'Traceback' not in output
    assert 'Failed to push to remote repository.' not in output

    # Check output.
    assert 'Root ref is: v1.0.0' in output


@pytest.mark.parametrize('give_up', [False, True])
def test_race(tmpdir, local_docs_ghp, remote, urls, give_up):
    """Test with race condition where another process pushes to gh-pages causing a retry.

    :param tmpdir: pytest fixture.
    :param local_docs_ghp: conftest fixture.
    :param remote: conftest fixture.
    :param urls: conftest fixture.
    :param bool give_up: Cause multiple race conditions causing timeout/giveup.
    """
    local_other = tmpdir.ensure_dir('local_other')
    pytest.run(local_other, ['git', 'clone', remote, '--branch=gh-pages', '.'])

    # Prepare command.
    env = dict(os.environ, GIT_DIR=str(local_docs_ghp.join('.git')))
    command = ['sphinx-versioning', '--no-colors', 'push', '.', 'gh-pages', 'html/docs']
    output_lines = list()
    caused = False

    # Run.
    proc = Popen(command, cwd=str(local_docs_ghp), env=env, stdout=PIPE, stderr=STDOUT)
    for line in iter(proc.stdout.readline, b''):
        output_lines.append(line)
        if line.strip() == b'=> Building docs...':
            if give_up or not caused:
                # Cause race condition.
                local_other.join('README').write('changed', mode='a')
                pytest.run(local_other, ['git', 'commit', '-am', 'Cause race condition.'])
                pytest.run(local_other, ['git', 'push', 'origin', 'gh-pages'])
                caused = True
    output_lines.append(proc.communicate()[0])
    output = b''.join(output_lines).decode('utf-8')
    if give_up:
        assert proc.poll() != 0
    else:
        assert proc.poll() == 0
    assert caused

    # Verify.
    assert 'Traceback' not in output
    assert 'Building docs...' in output
    assert 'Failed to push to remote repository. Retrying in ' in output
    if give_up:
        assert 'Successfully pushed to remote repository.' not in output
        assert 'Ran out of retries, giving up.' in output
        return
    assert 'Successfully pushed to remote repository.' in output

    # Verify files.
    pytest.run(local_docs_ghp, ['git', 'checkout', 'gh-pages'])
    pytest.run(local_docs_ghp, ['git', 'pull', 'origin', 'gh-pages'])
    destination = local_docs_ghp.join('html', 'docs')
    urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])
    actual = local_docs_ghp.join('README').read()
    assert actual == 'Orphaned branch for HTML docs.changed'


def test_different_push(tmpdir, local_docs_ghp, urls):
    """Test pushing to a different remote URL.

    :param tmpdir: pytest fixture.
    :param local_docs_ghp: conftest fixture.
    :param urls: conftest fixture.
    """
    remote2 = tmpdir.ensure_dir('remote2')
    pytest.run(local_docs_ghp, ['git', 'remote', 'set-url', 'origin', '--push', remote2])

    # Error out because remote2 doesn't exist yet.
    with pytest.raises(CalledProcessError) as exc:
        pytest.run(local_docs_ghp, ['sphinx-versioning', 'push', '.', 'gh-pages', '.'])
    assert 'Traceback' not in exc.value.output
    assert 'Failed to push to remote.' in exc.value.output
    assert "remote2' does not appear to be a git repository" in exc.value.output

    # Create remote2.
    pytest.run(remote2, ['git', 'init', '--bare'])

    # Run again.
    output = pytest.run(local_docs_ghp, ['sphinx-versioning', 'push', '.', 'gh-pages', '.'])
    assert 'Traceback' not in output
    assert 'Successfully pushed to remote repository.' in output

    # Check files.
    pytest.run(local_docs_ghp, ['git', 'fetch', 'origin'])
    pytest.run(local_docs_ghp, ['git', 'checkout', 'origin/gh-pages'])
    assert not local_docs_ghp.join('contents.html').check()
    assert not local_docs_ghp.join('master').check()
    pytest.run(local_docs_ghp, ['git', 'remote', 'add', 'remote2', remote2])
    pytest.run(local_docs_ghp, ['git', 'fetch', 'remote2'])
    pytest.run(local_docs_ghp, ['git', 'checkout', 'remote2/gh-pages'])
    urls(local_docs_ghp.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(local_docs_ghp.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])


@pytest.mark.parametrize('remove', [True, False])
def test_second_remote(tmpdir, local_docs_ghp, urls, remove):
    """Test pushing to a non-origin remote without the original remote having the destination branch.

    :param tmpdir: pytest fixture.
    :param local_docs_ghp: conftest fixture.
    :param urls: conftest fixture.
    :param bool remove: Remove gh-pages from origin.
    """
    if remove:
        pytest.run(local_docs_ghp, ['git', 'push', 'origin', '--delete', 'gh-pages'])

    # Create remote2.
    remote2 = tmpdir.ensure_dir('remote2')
    pytest.run(remote2, ['git', 'init', '--bare'])
    local2 = tmpdir.ensure_dir('local2')
    pytest.run(local2, ['git', 'clone', remote2, '.'])
    pytest.run(local2, ['git', 'checkout', '-b', 'gh-pages'])
    local2.ensure('README')
    pytest.run(local2, ['git', 'add', 'README'])
    pytest.run(local2, ['git', 'commit', '-m', 'Initial commit.'])
    pytest.run(local2, ['git', 'push', 'origin', 'gh-pages'])
    pytest.run(local_docs_ghp, ['git', 'remote', 'add', 'remote2', remote2])
    pytest.run(local_docs_ghp, ['git', 'fetch', 'remote2'])

    # Run.
    output = pytest.run(local_docs_ghp, ['sphinx-versioning', 'push', '.', 'gh-pages', '.', '-P', 'remote2'])
    assert 'Traceback' not in output
    assert 'Successfully pushed to remote repository.' in output

    # Check files.
    pytest.run(local_docs_ghp, ['git', 'fetch', 'remote2'])
    pytest.run(local_docs_ghp, ['git', 'checkout', 'remote2/gh-pages'])
    urls(local_docs_ghp.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(local_docs_ghp.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])
    if remove:
        with pytest.raises(CalledProcessError) as exc:
            pytest.run(local_docs_ghp, ['git', 'checkout', 'origin/gh-pages'])
        assert "origin/gh-pages' did not match any file(s) known to git" in exc.value.output
    else:
        pytest.run(local_docs_ghp, ['git', 'checkout', 'origin/gh-pages'])
        pytest.run(local_docs_ghp, ['git', 'pull', 'origin', 'gh-pages'])
        assert not local_docs_ghp.join('contents.html').check()
        assert not local_docs_ghp.join('master').check()

    # Run again.
    pytest.run(local_docs_ghp, ['git', 'checkout', 'master'])
    local_docs_ghp.join('contents.rst').write('\nNew Line Added\n', mode='a')
    pytest.run(local_docs_ghp, ['git', 'commit', '-am', 'Adding new line.'])
    pytest.run(local_docs_ghp, ['git', 'push', 'origin', 'master'])
    output = pytest.run(local_docs_ghp, ['sphinx-versioning', 'push', '.', 'gh-pages', '.', '-P', 'remote2'])
    assert 'Traceback' not in output
    assert 'Successfully pushed to remote repository.' in output

    # Check files.
    pytest.run(local_docs_ghp, ['git', 'fetch', 'remote2'])
    pytest.run(local_docs_ghp, ['git', 'checkout', 'remote2/gh-pages'])
    urls(local_docs_ghp.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(local_docs_ghp.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])
    contents = local_docs_ghp.join('contents.html').read()
    assert 'New Line Added' in contents
    if remove:
        with pytest.raises(CalledProcessError) as exc:
            pytest.run(local_docs_ghp, ['git', 'checkout', 'origin/gh-pages'])
        assert "origin/gh-pages' did not match any file(s) known to git" in exc.value.output
    else:
        pytest.run(local_docs_ghp, ['git', 'checkout', 'origin/gh-pages'])
        pytest.run(local_docs_ghp, ['git', 'pull', 'origin', 'gh-pages'])
        assert not local_docs_ghp.join('contents.html').check()
        assert not local_docs_ghp.join('master').check()


def test_error_clone_failure(local_docs):
    """Test DEST_BRANCH doesn't exist.

    :param local_docs: conftest fixture.
    """
    # Run.
    with pytest.raises(CalledProcessError) as exc:
        pytest.run(local_docs, ['sphinx-versioning', 'push', '.', 'gh-pages', '.'])
    assert 'Traceback' not in exc.value.output
    assert 'Cloning gh-pages into temporary directory...' in exc.value.output
    assert 'Failed to clone from remote repo URL.' in exc.value.output
    assert 'fatal: Remote branch gh-pages not found in upstream origin' in exc.value.output


def test_error_build_failure(local_docs_ghp):
    """Test HandledError in main_build().

    :param local_docs_ghp: conftest fixture.
    """
    local_docs_ghp.join('conf.py').write('undefined')
    pytest.run(local_docs_ghp, ['git', 'commit', '-am', 'Cause build failure.'])
    pytest.run(local_docs_ghp, ['git', 'push', 'origin', 'master'])

    # Run.
    with pytest.raises(CalledProcessError) as exc:
        pytest.run(local_docs_ghp, ['sphinx-versioning', '-L', 'push', '.', 'gh-pages', '.'])
    assert exc.value.output.count('Traceback') == 1
    assert "name 'undefined' is not defined" in exc.value.output
    assert 'Building docs...' in exc.value.output
    assert 'sphinx-build failed for branch/tag: master' in exc.value.output
    assert exc.value.output.strip().endswith('Failure.')


def test_bad_git_config(local_docs_ghp):
    """Git commit fails.

    Need to do the crazy Popen thing since the local repo being committed to is the gh-pages temporary repo.

    :param local_docs_ghp: conftest fixture.
    """
    env = dict(os.environ, GIT_DIR=str(local_docs_ghp.join('.git')), HOME=str(local_docs_ghp.join('..')))
    command = ['sphinx-versioning', '-v', 'push', '.', 'gh-pages', '.']
    output_lines = list()
    caused = False

    # Run.
    proc = Popen(command, cwd=str(local_docs_ghp), env=env, stdout=PIPE, stderr=STDOUT)
    for line in iter(proc.stdout.readline, b''):
        output_lines.append(line)
        if b'"command": ["git", "clone"' in line:
            if not caused:
                # Invalidate lock file.
                tmp_repo = py.path.local(re.findall(r'"cwd": "([^"]+)"', line.decode('utf-8'))[0])
                assert tmp_repo.check(dir=True)
                pytest.run(tmp_repo, ['git', 'config', 'user.useConfigOnly', 'true'], retry=3)
                pytest.run(tmp_repo, ['git', 'config', 'user.email', '(none)'], retry=3)
                caused = True
    output_lines.append(proc.communicate()[0])
    output = b''.join(output_lines).decode('utf-8')
    assert proc.poll() != 0
    assert caused

    # Verify.
    assert 'Traceback' not in output
    assert 'Failed to commit locally.' in output
    assert 'Please tell me who you are.' in output or 'user.useConfigOnly set but no name given' in output
