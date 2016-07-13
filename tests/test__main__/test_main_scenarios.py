"""Test calls to main() with different command line options."""

from subprocess import CalledProcessError

import pytest


def test_sub_page_and_tag(tmpdir, local_docs, run):
    """Test with sub pages and one git tag. Testing with chdir.

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


def test_moved_docs_many(tmpdir, local_docs, run):
    """Test with additional sources. Testing without chdir. Non-created destination.

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
    run(tmpdir, ['sphinx-versioning', 'build', str(local_docs), str(destination), '-s', 'docs', '-s', 'docs2'])

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


def test_error_bad_path(tmpdir, run):
    """Test handling of bad paths.

    :param tmpdir: pytest fixture.
    :param run: conftest fixture.
    """
    with pytest.raises(CalledProcessError) as exc:
        run(tmpdir, ['sphinx-versioning', 'build', 'unknown', str(tmpdir)])
    assert 'Path not found: unknown\n' in exc.value.output

    with pytest.raises(CalledProcessError) as exc:
        run(tmpdir, ['sphinx-versioning', 'build', str(tmpdir.ensure('is_file')), str(tmpdir)])
    assert 'Path not a directory: {}\n'.format(tmpdir.join('is_file')) in exc.value.output

    with pytest.raises(CalledProcessError) as exc:
        run(tmpdir, ['sphinx-versioning', 'build', '.', str(tmpdir)])
    assert 'Failed to find local git repository root.' in exc.value.output


def test_error_no_docs_found(tmpdir, local, run):
    """Test no docs to build.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param run: conftest fixture.
    """
    with pytest.raises(CalledProcessError) as exc:
        run(local, ['sphinx-versioning', 'build', '.', str(tmpdir), '-v'])
    assert 'No docs found in any remote branch/tag. Nothing to do.\n' in exc.value.output


def test_error_bad_root_ref(tmpdir, local_docs, run):
    """Test bad root ref.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    with pytest.raises(CalledProcessError) as exc:
        run(local_docs, ['sphinx-versioning', 'build', '.', str(tmpdir), '-v', '-r', 'unknown'])
    assert 'Root ref unknown not found in: master\n' in exc.value.output
