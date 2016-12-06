"""Test function in module."""

from os.path import join
from subprocess import CalledProcessError

import pytest

from sphinxcontrib.versioning.git import export, fetch_commits, IS_WINDOWS, list_remote


def test_simple(tmpdir, local):
    """Test with just the README in one commit.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    """
    target = tmpdir.ensure_dir('target')
    sha = pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip()

    export(str(local), sha, str(target))
    pytest.run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])  # Exit 0 if nothing changed.
    files = [f.relto(target) for f in target.listdir()]
    assert files == ['README']


def test_overwrite(tmpdir, local):
    """Test overwriting existing files.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    """
    local.ensure('docs', '_templates', 'layout.html').write('three')
    local.join('docs', 'conf.py').write('one')
    local.join('docs', 'index.rst').write('two')
    pytest.run(local, ['git', 'add', 'docs'])
    pytest.run(local, ['git', 'commit', '-m', 'Added docs dir.'])
    pytest.run(local, ['git', 'push', 'origin', 'master'])
    sha = pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip()

    target = tmpdir.ensure_dir('target')
    target.ensure('docs', '_templates', 'other', 'other.html').write('other')
    target.join('docs', '_templates', 'other.html').write('other')
    target.ensure('docs', 'other', 'other.py').write('other')
    target.join('docs', 'other.rst').write('other')

    export(str(local), sha, str(target))
    pytest.run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])

    expected = [
        'README',
        'docs',
        join('docs', '_templates'),
        join('docs', '_templates', 'layout.html'),
        join('docs', '_templates', 'other'),
        join('docs', '_templates', 'other.html'),
        join('docs', '_templates', 'other', 'other.html'),
        join('docs', 'conf.py'),
        join('docs', 'index.rst'),
        join('docs', 'other'),
        join('docs', 'other.rst'),
        join('docs', 'other', 'other.py'),
    ]
    paths = sorted(f.relto(target) for f in target.visit())
    assert paths == expected


@pytest.mark.usefixtures('outdate_local')
@pytest.mark.parametrize('fail', [False, True])
def test_new_branch_tags(tmpdir, local_light, fail):
    """Test with new branches and tags unknown to local repo.

    :param tmpdir: pytest fixture.
    :param local_light: conftest fixture.
    :param bool fail: Fail by not fetching.
    """
    remotes = [r for r in list_remote(str(local_light)) if r[1] == 'ob_at']

    # Fail.
    sha = remotes[0][0]
    target = tmpdir.ensure_dir('exported', sha)
    if fail:
        with pytest.raises(CalledProcessError):
            export(str(local_light), sha, str(target))
        return

    # Fetch.
    fetch_commits(str(local_light), remotes)

    # Export.
    export(str(local_light), sha, str(target))
    files = [f.relto(target) for f in target.listdir()]
    assert files == ['README']
    assert target.join('README').read() == 'new'


@pytest.mark.skipif(str(IS_WINDOWS))
def test_symlink(tmpdir, local):
    """Test repos with broken symlinks.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    """
    orphan = tmpdir.ensure('to_be_removed')
    local.join('good_symlink').mksymlinkto('README')
    local.join('broken_symlink').mksymlinkto('to_be_removed')
    pytest.run(local, ['git', 'add', 'good_symlink', 'broken_symlink'])
    pytest.run(local, ['git', 'commit', '-m', 'Added symlinks.'])
    pytest.run(local, ['git', 'push', 'origin', 'master'])
    orphan.remove()

    target = tmpdir.ensure_dir('target')
    sha = pytest.run(local, ['git', 'rev-parse', 'HEAD']).strip()

    export(str(local), sha, str(target))
    pytest.run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])  # Exit 0 if nothing changed.
    files = sorted(f.relto(target) for f in target.listdir())
    assert files == ['README', 'good_symlink']
