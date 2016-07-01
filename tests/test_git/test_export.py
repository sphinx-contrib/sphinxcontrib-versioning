"""Test function in module."""

from subprocess import CalledProcessError

import pytest

from sphinxcontrib.versioning.git import export, fetch_commits, list_remote


def test_simple(tmpdir, local, run):
    """Test with just the README in one commit.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param run: conftest fixture.
    """
    target = tmpdir.ensure_dir('target')
    sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()

    export(str(local), ['README'], sha, str(target))
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])  # Exit 0 if nothing changed.
    files = [f.relto(target) for f in target.listdir()]
    assert files == ['README']


def test_overwrite(tmpdir, local, run):
    """Test overwriting existing files.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param run: conftest fixture.
    """
    local.ensure('docs', '_templates', 'layout.html').write('three')
    local.join('docs', 'conf.py').write('one')
    local.join('docs', 'index.rst').write('two')
    run(local, ['git', 'add', 'docs'])
    run(local, ['git', 'commit', '-m', 'Added docs dir.'])
    run(local, ['git', 'push', 'origin', 'master'])
    sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()

    target = tmpdir.ensure_dir('target')
    target.ensure('_templates', 'other', 'other.html').write('other')
    target.join('_templates', 'other.html').write('other')
    target.ensure('other', 'other.py').write('other')
    target.join('other.rst').write('other')

    export(str(local), ['docs/conf.py'], sha, str(target))
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])

    expected = [
        '_templates',
        '_templates/layout.html',
        '_templates/other',
        '_templates/other.html',
        '_templates/other/other.html',
        'conf.py',
        'index.rst',
        'other',
        'other.rst',
        'other/other.py',
    ]
    paths = sorted(f.relto(target) for f in target.visit())
    assert paths == expected


@pytest.mark.parametrize('levels', range(1, 4))
def test_docs_dir(tmpdir, local, run, levels):
    """Test with docs subdirectory.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param run: conftest fixture.
    :param int levels: Number of subdirectories to put files in.
    """
    docs = local
    for _ in range(levels):
        docs = docs.ensure_dir('docs')
    docs.join('conf.py').write('one')
    docs.join('index.rst').write('two')
    docs.ensure('_templates', 'layout.html').write('three')
    run(local, ['git', 'add', '.'])
    run(local, ['git', 'commit', '-m', 'Added docs dir.'])
    run(local, ['git', 'push', 'origin', 'master'])

    conf_rel_paths = [
        'docs/docs/docs/docs/docs/conf.py',
        'docs/docs/docs/docs/conf.py',
        'docs/docs/docs/conf.py',
        'docs/docs/conf.py',
        'docs/conf.py',
        'conf.py',
    ]
    sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()
    target = tmpdir.ensure_dir('target')
    export(str(local), conf_rel_paths, sha, str(target))
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])

    expected = ['_templates', '_templates/layout.html', 'conf.py', 'index.rst']
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
            export(str(local_light), ['README'], sha, str(target))
        return

    # Fetch.
    fetch_commits(str(local_light), remotes)

    # Export.
    export(str(local_light), ['README'], sha, str(target))
    files = [f.relto(target) for f in target.listdir()]
    assert files == ['README']
    assert target.join('README').read() == 'new'
