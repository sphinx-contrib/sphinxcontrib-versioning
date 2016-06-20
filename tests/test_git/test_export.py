"""Test function in module."""

import os

import pytest

from sphinxcontrib.versioning.git import export


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
