"""Test function in module."""

import os

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

    export(str(local), '.', sha, str(target))
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])  # Exit 0 if nothing changed.
    files = [f.relto(target) for f in target.listdir()]
    assert files == ['README']


@pytest.mark.parametrize('levels', range(1, 4))
def test_docs_dir(tmpdir, local, run, levels):
    """Test with docs subdirectory.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param run: conftest fixture.
    :param int levels: Number of subdirectories to put files in.
    """
    docs = local
    docs_rel_path = ''
    expected = ['conf.py', 'index.rst', '_templates', '_templates/layout.html']
    for _ in range(levels):
        docs = docs.ensure_dir('docs')
        docs_rel_path = os.path.join(docs_rel_path, 'docs')
        expected = [os.path.join('docs', i) for i in expected]
        expected.append('docs')
    docs.join('conf.py').write('one')
    docs.join('index.rst').write('two')
    docs.ensure('_templates', 'layout.html').write('three')
    run(local, ['git', 'add', '.'])
    run(local, ['git', 'commit', '-m', 'Added docs dir.'])
    run(local, ['git', 'push', 'origin', 'master'])

    target = tmpdir.ensure_dir('target')
    sha = run(local, ['git', 'rev-parse', 'HEAD']).strip()

    export(str(local), docs_rel_path, sha, str(target))
    run(local, ['git', 'diff-index', '--quiet', 'HEAD', '--'])
    paths = sorted(f.relto(target) for f in target.visit())
    expected.sort()
    assert paths == expected


@pytest.mark.usefixtures('local')
@pytest.mark.parametrize('mode', ['pushed_tag_of_unpushed_branch', 'annotated_tag_orphaned_branch'])
def test_new_branch_tags(tmpdir, remote, run, mode):
    """Test with new branches and tags unknown to local repo.

    :param tmpdir: pytest fixture.
    :param remote: conftest fixture.
    :param run: conftest fixture.
    :param str mode: Test scenario.
    """
    # Setup other behind local with just one cloned branch.
    local = tmpdir.ensure_dir('local2')
    run(local, ['git', 'clone', '--depth=1', '--branch=feature', remote, '.'])
    run(local, ['git', 'checkout', '-qf', run(local, ['git', 'rev-parse', 'HEAD']).strip()])

    # Commit to separate local repo and push to common remote.
    local_ahead = tmpdir.ensure_dir('local_ahead')
    run(local_ahead, ['git', 'clone', remote, '.'])
    if mode == 'pushed_tag_of_unpushed_branch':
        run(local_ahead, ['git', 'checkout', '-b', 'un_pushed_branch'])
        local_ahead.join('README').write('one')
        run(local_ahead, ['git', 'commit', '-am', 'Changed new branch'])
        sha = run(local_ahead, ['git', 'rev-parse', 'HEAD']).strip()
        run(local_ahead, ['git', 'tag', 'nb_tag'])
        run(local_ahead, ['git', 'push', 'origin', 'nb_tag'])
    else:
        run(local_ahead, ['git', 'checkout', '--orphan', 'orphaned_branch'])
        local_ahead.join('README').write('two')
        run(local_ahead, ['git', 'add', 'README'])
        run(local_ahead, ['git', 'commit', '-m', 'Added new README'])
        sha = run(local_ahead, ['git', 'rev-parse', 'HEAD']).strip()
        run(local_ahead, ['git', 'tag', '--annotate', '-m', 'Tag annotation.', 'ob_at'])
        run(local_ahead, ['git', 'push', 'origin', 'orphaned_branch', 'ob_at'])

    # Fetch.
    remotes = [r for r in list_remote(str(local)) if r[0] == sha]
    assert remotes
    fetch_commits(str(local), remotes)

    # Export.
    target = tmpdir.ensure_dir('exported', sha)
    export(str(local), '.', sha, str(target))
    files = [f.relto(target) for f in target.listdir()]
    assert files == ['README']
    expected = 'one' if mode == 'pushed_tag_of_unpushed_branch' else 'two'
    assert target.join('README').read() == expected
