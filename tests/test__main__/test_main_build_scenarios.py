"""Test calls to main() with different command line options."""

import time
from subprocess import CalledProcessError

import pytest


def test_sub_page_and_tag(tmpdir, local_docs, run, urls):
    """Test with sub pages and one git tag. Testing from local git repo.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param urls: conftest fixture.
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
    output = run(local_docs, ['sphinx-versioning', 'build', '.', str(destination)])
    assert 'Traceback' not in output

    # Check root.
    urls(destination.join('contents.html'), [
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>'
    ])
    urls(destination.join('subdir', 'sub.html'), [
        '<li><a href="../master/subdir/sub.html">master</a></li>',
        '<li><a href="../v1.0.0/subdir/sub.html">v1.0.0</a></li>',
    ])

    # Check master.
    urls(destination.join('master', 'contents.html'), [
        '<li><a href="contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
    ])
    urls(destination.join('master', 'subdir', 'sub.html'), [
        '<li><a href="sub.html">master</a></li>',
        '<li><a href="../../v1.0.0/subdir/sub.html">v1.0.0</a></li>',
    ])

    # Check v1.0.0.
    urls(destination.join('v1.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="contents.html">v1.0.0</a></li>',
    ])
    urls(destination.join('v1.0.0', 'subdir', 'sub.html'), [
        '<li><a href="../../master/subdir/sub.html">master</a></li>',
        '<li><a href="sub.html">v1.0.0</a></li>',
    ])


def test_moved_docs(tmpdir, local_docs, run, urls):
    """Test with docs being in their own directory.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param urls: conftest fixture.
    """
    run(local_docs, ['git', 'tag', 'v1.0.0'])  # Ignored since we only specify 'docs' in the command below.
    local_docs.ensure_dir('docs')
    run(local_docs, ['git', 'mv', 'conf.py', 'docs/conf.py'])
    run(local_docs, ['git', 'mv', 'contents.rst', 'docs/contents.rst'])
    run(local_docs, ['git', 'commit', '-m', 'Moved docs.'])
    run(local_docs, ['git', 'push', 'origin', 'master', 'v1.0.0'])

    # Run.
    destination = tmpdir.join('destination')
    output = run(local_docs, ['sphinx-versioning', 'build', 'docs', str(destination)])
    assert 'Traceback' not in output

    # Check master.
    urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])


def test_moved_docs_many(tmpdir, local_docs, run, urls):
    """Test with additional sources. Testing with --chdir. Non-created destination.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param urls: conftest fixture.
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
    output = run(tmpdir, ['sphinx-versioning', '-c', str(local_docs), 'build', 'docs', 'docs2', '.', str(destination)])
    assert 'Traceback' not in output

    # Check root.
    urls(destination.join('contents.html'), [
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="v1.0.1/contents.html">v1.0.1</a></li>',
        '<li><a href="v1.0.2/contents.html">v1.0.2</a></li>',
    ])

    # Check master, v1.0.0, v1.0.1, v1.0.2.
    urls(destination.join('master', 'contents.html'), [
        '<li><a href="contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.0.1/contents.html">v1.0.1</a></li>',
        '<li><a href="../v1.0.2/contents.html">v1.0.2</a></li>',
    ])
    urls(destination.join('v1.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.0.1/contents.html">v1.0.1</a></li>',
        '<li><a href="../v1.0.2/contents.html">v1.0.2</a></li>',
    ])
    urls(destination.join('v1.0.1', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="contents.html">v1.0.1</a></li>',
        '<li><a href="../v1.0.2/contents.html">v1.0.2</a></li>',
    ])
    urls(destination.join('v1.0.2', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.0.1/contents.html">v1.0.1</a></li>',
        '<li><a href="contents.html">v1.0.2</a></li>',
    ])


def test_version_change(tmpdir, local_docs, run, urls):
    """Verify new links are added and old links are removed when only changing versions. Using the same doc files.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param urls: conftest fixture.
    """
    destination = tmpdir.join('destination')

    # Only master.
    output = run(local_docs, ['sphinx-versioning', 'build', '.', 'docs', str(destination)])
    assert 'Traceback' not in output
    urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])

    # Add tags.
    run(local_docs, ['git', 'tag', 'v1.0.0'])
    run(local_docs, ['git', 'tag', 'v2.0.0'])
    run(local_docs, ['git', 'push', 'origin', 'v1.0.0', 'v2.0.0'])
    output = run(local_docs, ['sphinx-versioning', 'build', '.', 'docs', str(destination)])
    assert 'Traceback' not in output
    urls(destination.join('contents.html'), [
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="v2.0.0/contents.html">v2.0.0</a></li>',
    ])

    urls(destination.join('master', 'contents.html'), [
        '<li><a href="contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])

    urls(destination.join('v1.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="contents.html">v1.0.0</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])

    urls(destination.join('v2.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="contents.html">v2.0.0</a></li>',
    ])

    # Remove one tag.
    run(local_docs, ['git', 'push', 'origin', '--delete', 'v2.0.0'])
    output = run(local_docs, ['sphinx-versioning', 'build', '.', 'docs', str(destination)])
    assert 'Traceback' not in output
    urls(destination.join('contents.html'), [
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>',
    ])

    urls(destination.join('master', 'contents.html'), [
        '<li><a href="contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
    ])

    urls(destination.join('v1.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="contents.html">v1.0.0</a></li>',
    ])


@pytest.mark.usefixtures('local_docs')
def test_multiple_local_repos(tmpdir, run, urls):
    """Test from another git repo as the current working directory.

    :param tmpdir: pytest fixture.
    :param run: conftest fixture.
    :param urls: conftest fixture.
    """
    other = tmpdir.ensure_dir('other')
    run(other, ['git', 'init'])

    # Run.
    destination = tmpdir.ensure_dir('destination')
    output = run(other, ['sphinx-versioning', '-c', '../local', '-v', 'build', '.', str(destination)])
    assert 'Traceback' not in output

    # Check.
    urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])


@pytest.mark.parametrize('no_tags', [False, True])
def test_root_ref(tmpdir, local_docs, run, no_tags):
    """Test --root-ref and friends.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param bool no_tags: Don't push tags. Test fallback handling.
    """
    local_docs.join('conf.py').write(
        'templates_path = ["_templates"]\n'
        'html_sidebars = {"**": ["custom.html"]}\n'
    )
    local_docs.ensure('_templates', 'custom.html').write(
        '<h3>Custom Sidebar</h3>\n'
        '<ul>\n'
        '<li>Current version: {{ current_version }}</li>\n'
        '</ul>\n'
    )
    run(local_docs, ['git', 'add', 'conf.py', '_templates'])
    run(local_docs, ['git', 'commit', '-m', 'Displaying version.'])
    time.sleep(1.5)
    if not no_tags:
        run(local_docs, ['git', 'tag', 'v2.0.0'])
        time.sleep(1.5)
        run(local_docs, ['git', 'tag', 'v1.0.0'])
    run(local_docs, ['git', 'checkout', '-b', 'f2'])
    run(local_docs, ['git', 'push', 'origin', 'master', 'f2'] + ([] if no_tags else ['v1.0.0', 'v2.0.0']))

    for arg, expected in (('--root-ref=f2', 'f2'), ('--greatest-tag', 'v2.0.0'), ('--recent-tag', 'v1.0.0')):
        # Run.
        destination = tmpdir.join('destination', arg[2:])
        output = run(tmpdir, ['sphinx-versioning', '-N', '-c', str(local_docs), 'build', '.', str(destination), arg])
        assert 'Traceback' not in output
        # Check root.
        contents = destination.join('contents.html').read()
        if no_tags and expected != 'f2':
            expected = 'master'
        assert 'Current version: {}'.format(expected) in contents
        # Check warning.
        if no_tags and 'tag' in arg:
            assert 'No git tags with docs found in remote. Falling back to --root-ref value.' in output
        else:
            assert 'No git tags with docs found in remote. Falling back to --root-ref value.' not in output
        # Check output.
        assert 'Root ref is: {}\n'.format(expected) in output


@pytest.mark.parametrize('parallel', [False, True])
def test_add_remove_docs(tmpdir, local_docs, run, urls, parallel):
    """Test URLs to other versions of current page with docs that are added/removed between versions.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param urls: conftest fixture.
    :param bool parallel: Run sphinx-build with -j option.
    """
    run(local_docs, ['git', 'tag', 'v1.0.0'])

    # Move once.
    local_docs.ensure_dir('sub')
    run(local_docs, ['git', 'mv', 'two.rst', 'too.rst'])
    run(local_docs, ['git', 'mv', 'three.rst', 'sub/three.rst'])
    local_docs.join('contents.rst').write(
        'Test\n'
        '====\n'
        '\n'
        'Sample documentation.\n'
        '\n'
        '.. toctree::\n'
        '    one\n'
        '    too\n'
        '    sub/three\n'
    )
    local_docs.join('too.rst').write(
        '.. _too:\n'
        '\n'
        'Too\n'
        '===\n'
        '\n'
        'Sub page documentation 2 too.\n'
    )
    run(local_docs, ['git', 'commit', '-am', 'Moved.'])
    run(local_docs, ['git', 'tag', 'v1.1.0'])
    run(local_docs, ['git', 'tag', 'v1.1.1'])

    # Delete.
    run(local_docs, ['git', 'rm', 'too.rst', 'sub/three.rst'])
    local_docs.join('contents.rst').write(
        'Test\n'
        '====\n'
        '\n'
        'Sample documentation.\n'
        '\n'
        '.. toctree::\n'
        '    one\n'
    )
    run(local_docs, ['git', 'commit', '-am', 'Deleted.'])
    run(local_docs, ['git', 'tag', 'v2.0.0'])
    run(local_docs, ['git', 'push', 'origin', 'v1.0.0', 'v1.1.0', 'v1.1.1', 'v2.0.0', 'master'])

    # Run.
    destination = tmpdir.ensure_dir('destination')
    overflow = ['--', '-j', '2'] if parallel else []
    output = run(local_docs, ['sphinx-versioning', 'build', '.', str(destination)] + overflow)
    assert 'Traceback' not in output

    # Check parallel.
    if parallel:
        assert 'waiting for workers' in output
    else:
        assert 'waiting for workers' not in output

    # Check root.
    urls(destination.join('contents.html'), [
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('one.html'), [
        '<li><a href="master/one.html">master</a></li>',
        '<li><a href="v1.0.0/one.html">v1.0.0</a></li>',
        '<li><a href="v1.1.0/one.html">v1.1.0</a></li>',
        '<li><a href="v1.1.1/one.html">v1.1.1</a></li>',
        '<li><a href="v2.0.0/one.html">v2.0.0</a></li>',
    ])

    # Check master.
    urls(destination.join('master', 'contents.html'), [
        '<li><a href="contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('master', 'one.html'), [
        '<li><a href="one.html">master</a></li>',
        '<li><a href="../v1.0.0/one.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/one.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/one.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/one.html">v2.0.0</a></li>',
    ])

    # Check v2.0.0.
    urls(destination.join('v2.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v2.0.0', 'one.html'), [
        '<li><a href="../master/one.html">master</a></li>',
        '<li><a href="../v1.0.0/one.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/one.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/one.html">v1.1.1</a></li>',
        '<li><a href="one.html">v2.0.0</a></li>',
    ])

    # Check v1.1.1.
    urls(destination.join('v1.1.1', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="contents.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.1.1', 'one.html'), [
        '<li><a href="../master/one.html">master</a></li>',
        '<li><a href="../v1.0.0/one.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/one.html">v1.1.0</a></li>',
        '<li><a href="one.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/one.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.1.1', 'too.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/too.html">v1.1.0</a></li>',
        '<li><a href="too.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.1.1', 'sub', 'three.html'), [
        '<li><a href="../../master/contents.html">master</a></li>',
        '<li><a href="../../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="../../v1.1.0/sub/three.html">v1.1.0</a></li>',
        '<li><a href="three.html">v1.1.1</a></li>',
        '<li><a href="../../v2.0.0/contents.html">v2.0.0</a></li>',
    ])

    # Check v1.1.0.
    urls(destination.join('v1.1.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="contents.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.1.0', 'one.html'), [
        '<li><a href="../master/one.html">master</a></li>',
        '<li><a href="../v1.0.0/one.html">v1.0.0</a></li>',
        '<li><a href="one.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/one.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/one.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.1.0', 'too.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="too.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/too.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.1.0', 'sub', 'three.html'), [
        '<li><a href="../../master/contents.html">master</a></li>',
        '<li><a href="../../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="three.html">v1.1.0</a></li>',
        '<li><a href="../../v1.1.1/sub/three.html">v1.1.1</a></li>',
        '<li><a href="../../v2.0.0/contents.html">v2.0.0</a></li>',
    ])

    # Check v1.0.0.
    urls(destination.join('v1.0.0', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="contents.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.0.0', 'one.html'), [
        '<li><a href="../master/one.html">master</a></li>',
        '<li><a href="one.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/one.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/one.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/one.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.0.0', 'two.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="two.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])
    urls(destination.join('v1.0.0', 'three.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="three.html">v1.0.0</a></li>',
        '<li><a href="../v1.1.0/contents.html">v1.1.0</a></li>',
        '<li><a href="../v1.1.1/contents.html">v1.1.1</a></li>',
        '<li><a href="../v2.0.0/contents.html">v2.0.0</a></li>',
    ])


@pytest.mark.parametrize('verbosity', [0, 1, 3])
def test_passing_verbose(local_docs, run, urls, verbosity):
    """Test setting sphinx-build verbosity.

    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param urls: conftest fixture.
    :param int verbosity: Number of -v to use.
    """
    command = ['sphinx-versioning'] + (['-v'] * verbosity) + ['build', '.', 'destination']

    # Run.
    output = run(local_docs, command)
    assert 'Traceback' not in output

    # Check master.
    destination = local_docs.join('destination')
    urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])

    # Check output.
    if verbosity == 0:
        assert 'INFO     sphinxcontrib.versioning.__main__' not in output
        assert 'docnames to write:' not in output
    elif verbosity == 1:
        assert 'INFO     sphinxcontrib.versioning.__main__' in output
        assert 'docnames to write:' not in output
    else:
        assert 'INFO     sphinxcontrib.versioning.__main__' in output
        assert 'docnames to write:' in output


def test_whitelisting(local_docs, run, urls):
    """Test whitelist features.

    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param urls: conftest fixture.
    """
    run(local_docs, ['git', 'tag', 'v1.0'])
    run(local_docs, ['git', 'tag', 'v1.0-dev'])
    run(local_docs, ['git', 'checkout', '-b', 'included', 'master'])
    run(local_docs, ['git', 'checkout', '-b', 'ignored', 'master'])
    run(local_docs, ['git', 'push', 'origin', 'v1.0', 'v1.0-dev', 'included', 'ignored'])

    command = [
        'sphinx-versioning', '-N', 'build', '.', 'html', '-w', 'master', '-w', 'included', '-W', '^v[0-9]+.[0-9]+$'
    ]

    # Run.
    output = run(local_docs, command)
    assert 'Traceback' not in output

    # Check output.
    assert 'With docs: ignored included master v1.0 v1.0-dev\n' in output
    assert 'Passed whitelisting: included master v1.0\n' in output

    # Check root.
    urls(local_docs.join('html', 'contents.html'), [
        '<li><a href="included/contents.html">included</a></li>',
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0/contents.html">v1.0</a></li>',
    ])


def test_error_bad_path(tmpdir, run):
    """Test handling of bad paths.

    :param tmpdir: pytest fixture.
    :param run: conftest fixture.
    """
    with pytest.raises(CalledProcessError) as exc:
        run(tmpdir, ['sphinx-versioning', '-N', '-c', 'unknown', 'build', '.', str(tmpdir)])
    assert 'Directory "unknown" does not exist.\n' in exc.value.output

    tmpdir.ensure('is_file')
    with pytest.raises(CalledProcessError) as exc:
        run(tmpdir, ['sphinx-versioning', '-N', '-c', 'is_file', 'build', '.', str(tmpdir)])
    assert 'Directory "is_file" is a file.\n' in exc.value.output

    with pytest.raises(CalledProcessError) as exc:
        run(tmpdir, ['sphinx-versioning', '-N', 'build', '.', str(tmpdir)])
    assert 'Failed to find local git repository root in {}.'.format(repr(str(tmpdir))) in exc.value.output

    repo = tmpdir.ensure_dir('repo')
    run(repo, ['git', 'init'])
    empty = tmpdir.ensure_dir('empty')
    with pytest.raises(CalledProcessError) as exc:
        run(repo, ['sphinx-versioning', '-N', '-g', str(empty), 'build', '.', str(tmpdir)])
    assert 'Failed to find local git repository root in {}.'.format(repr(str(empty))) in exc.value.output


def test_error_no_docs_found(tmpdir, local, run):
    """Test no docs to build.

    :param tmpdir: pytest fixture.
    :param local: conftest fixture.
    :param run: conftest fixture.
    """
    with pytest.raises(CalledProcessError) as exc:
        run(local, ['sphinx-versioning', '-N', '-v', 'build', '.', str(tmpdir)])
    assert 'No docs found in any remote branch/tag. Nothing to do.\n' in exc.value.output


def test_error_bad_root_ref(tmpdir, local_docs, run):
    """Test bad root ref.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    """
    with pytest.raises(CalledProcessError) as exc:
        run(local_docs, ['sphinx-versioning', '-N', '-v', 'build', '.', str(tmpdir), '-r', 'unknown'])
    assert 'Root ref unknown not found in: master\n' in exc.value.output
