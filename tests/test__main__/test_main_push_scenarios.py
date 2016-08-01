"""Test calls to main() with different command line options."""

import os
import re
from subprocess import CalledProcessError, PIPE, Popen, STDOUT

import py
import pytest


def test_no_exclude(local_docs_ghp, run):
    """Test with successful push to remote. Don't remove/exclude any files.

    :param local_docs_ghp: conftest fixture.
    :param run: conftest fixture.
    """
    # Run.
    output = run(local_docs_ghp, ['sphinx-versioning', 'push', 'gh-pages', '.', '.'])
    assert 'Traceback' not in output
    assert 'Failed to push to remote repository.' not in output

    # Check HTML.
    run(local_docs_ghp, ['git', 'checkout', 'gh-pages'])
    run(local_docs_ghp, ['git', 'pull', 'origin', 'gh-pages'])
    contents = local_docs_ghp.join('contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents

    # Run again.
    output = run(local_docs_ghp, ['sphinx-versioning', 'push', 'gh-pages', '.', '.'])
    assert 'Traceback' not in output
    assert 'Failed to push to remote repository.' not in output
    assert 'No significant changes to commit.' in output

    # Check SHAs.
    old_sha = run(local_docs_ghp, ['git', 'rev-parse', 'HEAD']).strip()
    run(local_docs_ghp, ['git', 'pull', 'origin', 'gh-pages'])
    sha = run(local_docs_ghp, ['git', 'rev-parse', 'HEAD']).strip()
    assert sha == old_sha


def test_exclude(local_docs_ghp, run):
    """Test excluding files and REL_DST. Also test changing files.

    :param local_docs_ghp: conftest fixture.
    :param run: conftest fixture.
    """
    run(local_docs_ghp, ['git', 'checkout', 'gh-pages'])
    local_docs_ghp.ensure('documentation', 'delete.txt').write('a')
    local_docs_ghp.ensure('documentation', 'keep.txt').write('b')
    run(local_docs_ghp, ['git', 'add', 'documentation'])
    run(local_docs_ghp, ['git', 'commit', '-m', 'Adding files.'])
    run(local_docs_ghp, ['git', 'push', 'origin', 'gh-pages'])

    # Run.
    output = run(local_docs_ghp, ['sphinx-versioning', 'push', 'gh-pages', 'documentation', '.', '-e', 'keep.txt'])
    assert 'Traceback' not in output

    # Check files.
    run(local_docs_ghp, ['git', 'pull', 'origin', 'gh-pages'])
    contents = local_docs_ghp.join('documentation', 'contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents
    assert not local_docs_ghp.join('documentation', 'delete.txt').check()
    assert local_docs_ghp.join('documentation', 'keep.txt').check()

    # Change and commit.
    run(local_docs_ghp, ['git', 'checkout', 'master'])
    local_docs_ghp.join('contents.rst').write('\nNew Unexpected Line!\n', mode='a')
    run(local_docs_ghp, ['git', 'commit', '-am', 'Changing docs.'])
    run(local_docs_ghp, ['git', 'push', 'origin', 'master'])

    # Run.
    output = run(local_docs_ghp, ['sphinx-versioning', 'push', 'gh-pages', 'documentation', '.', '-e', 'keep.txt'])
    assert 'Traceback' not in output

    # Check files.
    run(local_docs_ghp, ['git', 'checkout', 'gh-pages'])
    run(local_docs_ghp, ['git', 'pull', 'origin', 'gh-pages'])
    contents = local_docs_ghp.join('documentation', 'contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents
    assert 'New Unexpected Line!' in contents
    assert not local_docs_ghp.join('documentation', 'delete.txt').check()
    assert local_docs_ghp.join('documentation', 'keep.txt').check()


@pytest.mark.parametrize('give_up', [False, True])
def test_race(tmpdir, local_docs_ghp, remote, run, give_up):
    """Test with race condition where another process pushes to gh-pages causing a retry.

    :param tmpdir: pytest fixture.
    :param local_docs_ghp: conftest fixture.
    :param remote: conftest fixture.
    :param run: conftest fixture.
    :param bool give_up: Cause multiple race conditions causing timeout/giveup.
    """
    local_other = tmpdir.ensure_dir('local_other')
    run(local_other, ['git', 'clone', remote, '--branch=gh-pages', '.'])

    # Prepare command.
    env = dict(os.environ, GIT_DIR=str(local_docs_ghp.join('.git')))
    command = ['sphinx-versioning', 'push', 'gh-pages', 'html/docs', '.', '--no-colors']
    output_lines = list()
    caused = False

    # Run.
    proc = Popen(command, cwd=str(local_docs_ghp), env=env, stdout=PIPE, stderr=STDOUT)
    for line in iter(proc.stdout.readline, b''):
        output_lines.append(line)
        if line == b'=> Building docs...\n':
            if give_up or not caused:
                # Cause race condition.
                local_other.join('README').write('changed', mode='a')
                run(local_other, ['git', 'commit', '-am', 'Cause race condition.'])
                run(local_other, ['git', 'push', 'origin', 'gh-pages'])
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
    run(local_docs_ghp, ['git', 'checkout', 'gh-pages'])
    run(local_docs_ghp, ['git', 'pull', 'origin', 'gh-pages'])
    contents = local_docs_ghp.join('html', 'docs', 'contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents
    actual = local_docs_ghp.join('README').read()
    assert actual == 'Orphaned branch for HTML docs.changed'


def test_error_clone_failure(local_docs, run):
    """Test DST_BRANCH doesn't exist.

    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    # Run.
    with pytest.raises(CalledProcessError) as exc:
        run(local_docs, ['sphinx-versioning', 'push', 'gh-pages', '.', '.'])
    assert 'Traceback' not in exc.value.output
    assert 'Cloning gh-pages into temporary directory...' in exc.value.output
    assert 'Failed to clone from remote repo URL.' in exc.value.output
    assert 'fatal: Remote branch gh-pages not found in upstream origin' in exc.value.output


def test_error_build_failure(local_docs_ghp, run):
    """Test HandledError in main_build().

    :param local_docs_ghp: conftest fixture.
    :param run: conftest fixture.
    """
    local_docs_ghp.join('conf.py').write('undefined')
    run(local_docs_ghp, ['git', 'commit', '-am', 'Cause build failure.'])
    run(local_docs_ghp, ['git', 'push', 'origin', 'master'])

    # Run.
    with pytest.raises(CalledProcessError) as exc:
        run(local_docs_ghp, ['sphinx-versioning', 'push', 'gh-pages', '.', '.'])
    assert exc.value.output.count('Traceback') == 1
    assert "name 'undefined' is not defined" in exc.value.output
    assert 'Building docs...' in exc.value.output
    assert 'sphinx-build failed for branch/tag: master' in exc.value.output
    assert exc.value.output.endswith('Failure.\n')


def test_bad_git_config(local_docs_ghp, run):
    """Git commit fails.

    Need to do the crazy Popen thing since the local repo being committed to is the gh-pages temporary repo.

    :param local_docs_ghp: conftest fixture.
    :param run: conftest fixture.
    """
    env = dict(os.environ, GIT_DIR=str(local_docs_ghp.join('.git')), HOME=str(local_docs_ghp.join('..')))
    command = ['sphinx-versioning', 'push', 'gh-pages', '.', '.', '-v']
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
                run(tmp_repo, ['git', 'config', 'user.useConfigOnly', 'true'])
                run(tmp_repo, ['git', 'config', 'user.email', '(none)'])
                caused = True
    output_lines.append(proc.communicate()[0])
    output = b''.join(output_lines).decode('utf-8')
    assert proc.poll() != 0
    assert caused

    # Verify.
    assert 'Traceback' not in output
    assert 'Failed to commit locally.' in output
    assert 'Please tell me who you are.' in output
