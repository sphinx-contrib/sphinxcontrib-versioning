"""Test function in module."""

from subprocess import CalledProcessError

import pytest

from sphinxcontrib.versioning.git import commit_and_push, GitError, WHITELIST_ENV_VARS


def test_whitelist():
    """Lint whitelist variable."""
    cleaned = sorted(set(WHITELIST_ENV_VARS))
    assert cleaned == sorted(WHITELIST_ENV_VARS)


@pytest.mark.parametrize('exclude', [False, True])
def test_nothing_to_commit(caplog, local, run, exclude):
    """Test with no changes to commit.

    :param caplog: pytest extension fixture.
    :param local: conftest fixture.
    :param run: conftest fixture.
    :param bool exclude: Test with exclude support (aka files staged for deletion). Else clean repo.
    """
    if exclude:
        contents = local.join('README').read()
        run(local, ['git', 'rm', 'README'])  # Stages removal of README.
        local.join('README').write(contents)  # Unstaged restore.
    old_sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()

    actual = commit_and_push(str(local))
    assert actual is True
    sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()
    assert sha == old_sha

    records = [(r.levelname, r.message) for r in caplog.records]
    assert ('INFO', 'No changes to commit.') in records


@pytest.mark.parametrize('subdirs', [False, True])
def test_nothing_significant_to_commit(caplog, local, run, subdirs):
    """Test ignoring of always-changing generated Sphinx files.

    :param caplog: pytest extension fixture.
    :param local: conftest fixture.
    :param run: conftest fixture.
    :param bool subdirs: Test these files from sub directories.
    """
    local.ensure('sub' if subdirs else '', '.doctrees', 'file.bin').write('data')
    local.ensure('sub' if subdirs else '', 'searchindex.js').write('data')
    old_sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()
    actual = commit_and_push(str(local))
    assert actual is True
    sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()
    assert sha != old_sha
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])  # Exit 0 if nothing changed.
    records = [(r.levelname, r.message) for r in caplog.records]
    assert ('INFO', 'No changes to commit.') not in records
    assert ('INFO', 'No significant changes to commit.') not in records

    local.ensure('sub' if subdirs else '', '.doctrees', 'file.bin').write('changed')
    local.ensure('sub' if subdirs else '', 'searchindex.js').write('changed')
    old_sha = sha
    records_seek = len(caplog.records)
    actual = commit_and_push(str(local))
    assert actual is True
    sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()
    assert sha == old_sha
    with pytest.raises(CalledProcessError):
        run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])
    records = [(r.levelname, r.message) for r in caplog.records][records_seek:]
    assert ('INFO', 'No changes to commit.') not in records
    assert ('INFO', 'No significant changes to commit.') in records

    local.join('README').write('changed')  # Should cause other two to be committed.
    old_sha = sha
    records_seek = len(caplog.records)
    actual = commit_and_push(str(local))
    assert actual is True
    sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()
    assert sha != old_sha
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])  # Exit 0 if nothing changed.
    records = [(r.levelname, r.message) for r in caplog.records][records_seek:]
    assert ('INFO', 'No changes to commit.') not in records
    assert ('INFO', 'No significant changes to commit.') not in records


def test_changes(monkeypatch, local, run):
    """Test with changes to commit and push successfully.

    :param monkeypatch: pytest fixture.
    :param local: conftest fixture.
    :param run: conftest fixture.
    """
    monkeypatch.setenv('TRAVIS_BUILD_ID', '12345')
    monkeypatch.setenv('TRAVIS_BRANCH', 'master')
    old_sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()
    local.ensure('new', 'new.txt')
    local.join('README').write('test\n', mode='a')

    actual = commit_and_push(str(local))
    assert actual is True
    sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()
    assert sha != old_sha
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])  # Exit 0 if nothing changed.

    # Verify commit message.
    subject, body = run(local, ['git', 'log', '-n1', '--pretty=%B']).strip().split('\n', 2)[::2]
    assert subject == 'AUTO: sphinxcontrib-versioning'
    assert body == 'LANG: en_US.UTF-8\nTRAVIS_BRANCH: master\nTRAVIS_BUILD_ID: 12345'


def test_branch_deleted(local, run):
    """Test scenario where branch is deleted by someone.

    :param local: conftest fixture.
    :param run: conftest fixture.
    """
    run(local, ['git', 'checkout', 'feature'])
    run(local, ['git', 'push', 'origin', '--delete', 'feature'])
    local.join('README').write('Changed by local.')

    # Run.
    actual = commit_and_push(str(local))
    assert actual is True
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])  # Exit 0 if nothing changed.
    assert local.join('README').read() == 'Changed by local.'


@pytest.mark.parametrize('collision', [False, True])
def test_retryable_race(tmpdir, local, remote, run, collision):
    """Test race condition scenario where another CI build pushes changes first.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param remote: conftest fixture.
    :param run: conftest fixture.
    :param bool collision: Have other repo make changes to the same file as this one.
    """
    local_other = tmpdir.ensure_dir('local_other')
    run(local_other, ['git', 'clone', remote, '.'])
    local_other.ensure('sub', 'ignored.txt').write('Added by other. Should be ignored by commit_and_push().')
    if collision:
        local_other.ensure('sub', 'added.txt').write('Added by other.')
    run(local_other, ['git', 'add', 'sub'])
    run(local_other, ['git', 'commit', '-m', 'Added by other.'])
    run(local_other, ['git', 'push', 'origin', 'master'])

    # Make unstaged changes and then run.
    local.ensure('sub', 'added.txt').write('Added by local.')
    actual = commit_and_push(str(local))

    # Verify.
    assert actual is False


def test_origin_deleted(local, remote):
    """Test scenario where the remote repo is unavailable (e.g. repo deleted from GitHub).

    :param local: conftest fixture.
    :param remote: conftest fixture.
    """
    local.join('README').write('Changed by local.')
    remote.remove()

    with pytest.raises(GitError) as exc:
        commit_and_push(str(local))
    assert 'Could not read from remote repository' in exc.value.output
