"""Test calls to main() with different command line options."""

from subprocess import CalledProcessError

import pytest


def test_sub_page_and_tag(tmpdir, local_docs, run):
    """Test with sub pages and one git tag. Testing from local git repo.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    local_docs.ensure('subdir', 'sub.rst').write(
        '.. _sub:\n'
        '\n'
        'Sub\n'
        '===\n'
        '\n'
        'Sub directory sub page documentation.\n'
    )
    local_docs.join('contents.rst').write('    subdir/sub\n', mode='a')
    run(local_docs, ['git', 'add', 'subdir', 'contents.rst'])
    run(local_docs, ['git', 'commit', '-m', 'Adding subdir docs.'])
    run(local_docs, ['git', 'tag', 'v1.0.0'])
    run(local_docs, ['git', 'push', 'origin', 'master', 'v1.0.0'])

    # Run.
    destination = tmpdir.ensure_dir('destination')
    run(local_docs, ['sphinx-versioning', 'build', '.', str(destination)])

    # Check master.
    contents = destination.join('contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents
    assert '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>' in contents
    contents = destination.join('subdir', 'sub.html').read()
    assert '<li><a href="../contents.html">master</a></li>' in contents
    assert '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>' in contents

    # Check v1.0.0.
    contents = destination.join('v1.0.0', 'contents.html').read()
    assert '<li><a href="../contents.html">master</a></li>' in contents
    assert '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>' in contents
    contents = destination.join('v1.0.0', 'subdir', 'sub.html').read()
    assert '<li><a href="../../contents.html">master</a></li>' in contents
    assert '<li><a href="../../v1.0.0/contents.html">v1.0.0</a></li>' in contents


def test_moved_docs(tmpdir, local_docs, run):
    """Test with docs being in their own directory.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    run(local_docs, ['git', 'tag', 'v1.0.0'])  # Ignored since we only specify 'docs' in the command below.
    local_docs.ensure_dir('docs')
    run(local_docs, ['git', 'mv', 'conf.py', 'docs/conf.py'])
    run(local_docs, ['git', 'mv', 'contents.rst', 'docs/contents.rst'])
    run(local_docs, ['git', 'commit', '-m', 'Moved docs.'])
    run(local_docs, ['git', 'push', 'origin', 'master', 'v1.0.0'])

    # Run.
    destination = tmpdir.join('destination')
    run(local_docs, ['sphinx-versioning', 'build', 'docs', str(destination)])

    # Check master.
    contents = destination.join('contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents
    assert 'v1.0' not in contents


def test_moved_docs_many(tmpdir, local_docs, run):
    """Test with additional sources. Testing with --chdir. Non-created destination.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    run(local_docs, ['git', 'tag', 'v1.0.0'])
    local_docs.ensure_dir('docs')
    run(local_docs, ['git', 'mv', 'conf.py', 'docs/conf.py'])
    run(local_docs, ['git', 'mv', 'contents.rst', 'docs/contents.rst'])
    run(local_docs, ['git', 'commit', '-m', 'Moved docs.'])
    run(local_docs, ['git', 'tag', 'v1.0.1'])
    local_docs.ensure_dir('docs2')
    run(local_docs, ['git', 'mv', 'docs/conf.py', 'docs2/conf.py'])
    run(local_docs, ['git', 'mv', 'docs/contents.rst', 'docs2/contents.rst'])
    run(local_docs, ['git', 'commit', '-m', 'Moved docs again.'])
    run(local_docs, ['git', 'tag', 'v1.0.2'])
    run(local_docs, ['git', 'push', 'origin', 'master', 'v1.0.0', 'v1.0.1', 'v1.0.2'])

    # Run.
    destination = tmpdir.join('destination')
    run(tmpdir,
        ['sphinx-versioning', 'build', '.', str(destination), '-c', str(local_docs), '-s', 'docs', '-s', 'docs2'])

    # Check master.
    contents = destination.join('contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents
    assert '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>' in contents
    assert '<li><a href="v1.0.1/contents.html">v1.0.1</a></li>' in contents
    assert '<li><a href="v1.0.2/contents.html">v1.0.2</a></li>' in contents

    # Check v1.0.0, v1.0.1, v1.0.2.
    for version in ('v1.0.0', 'v1.0.1', 'v1.0.2'):
        contents = destination.join(version, 'contents.html').read()
        assert '<li><a href="../contents.html">master</a></li>' in contents
        assert '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>' in contents
        assert '<li><a href="../v1.0.1/contents.html">v1.0.1</a></li>' in contents
        assert '<li><a href="../v1.0.2/contents.html">v1.0.2</a></li>' in contents


@pytest.mark.usefixtures('local_docs')
def test_multiple_local_repos(tmpdir, run):
    """Test from another git repo as the current working directory.

    :param tmpdir: pytest fixture.
    :param run: conftest fixture.
    """
    other = tmpdir.ensure_dir('other')
    run(other, ['git', 'init'])

    # Run.
    destination = tmpdir.ensure_dir('destination')
    run(other, ['sphinx-versioning', 'build', '.', str(destination), '-c', '../local', '-v'])

    # Check master.
    contents = destination.join('contents.html').read()
    assert '<li><a href="contents.html">master</a></li>' in contents


def test_error_bad_path(tmpdir, run):
    """Test handling of bad paths.

    :param tmpdir: pytest fixture.
    :param run: conftest fixture.
    """
    with pytest.raises(CalledProcessError) as exc:
        run(tmpdir, ['sphinx-versioning', 'build', '.', str(tmpdir), '-C', '-c', 'unknown'])
    assert 'Path not found: unknown\n' in exc.value.output

    tmpdir.ensure('is_file')
    with pytest.raises(CalledProcessError) as exc:
        run(tmpdir, ['sphinx-versioning', 'build', '.', str(tmpdir), '-C', '-c', 'is_file'])
    assert 'Path not a directory: is_file\n' in exc.value.output

    with pytest.raises(CalledProcessError) as exc:
        run(tmpdir, ['sphinx-versioning', 'build', '.', str(tmpdir), '-C'])
    assert 'Failed to find local git repository root.' in exc.value.output


def test_error_no_docs_found(tmpdir, local, run):
    """Test no docs to build.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param run: conftest fixture.
    """
    with pytest.raises(CalledProcessError) as exc:
        run(local, ['sphinx-versioning', 'build', '.', str(tmpdir), '-C', '-v'])
    assert 'No docs found in any remote branch/tag. Nothing to do.\n' in exc.value.output


def test_error_bad_root_ref(tmpdir, local_docs, run):
    """Test bad root ref.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    with pytest.raises(CalledProcessError) as exc:
        run(local_docs, ['sphinx-versioning', 'build', '.', str(tmpdir), '-C', '-v', '-r', 'unknown'])
    assert 'Root ref unknown not found in: master\n' in exc.value.output
