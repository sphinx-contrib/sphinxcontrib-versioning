"""Test function in module."""

import pytest

from sphinxcontrib.versioning.git import export
from sphinxcontrib.versioning.lib import HandledError
from sphinxcontrib.versioning.routines import build_all, gather_git_info
from sphinxcontrib.versioning.versions import Versions


def test_single(tmpdir, local_docs, urls):
    """With single version.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param urls: conftest fixture.
    """
    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))

    # Export.
    exported_root = tmpdir.ensure_dir('exported_root')
    export(str(local_docs), versions['master']['sha'], str(exported_root.join(versions['master']['sha'])))

    # Run and verify directory.
    destination = tmpdir.ensure_dir('destination')
    build_all(str(exported_root), str(destination), versions)
    actual = sorted(f.relto(destination) for f in destination.visit() if f.check(dir=True))
    expected = [
        '.doctrees',
        '_sources',
        '_static',
        'master',
        'master/.doctrees',
        'master/_sources',
        'master/_static',
    ]
    assert actual == expected

    # Verify HTML links.
    urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])


@pytest.mark.parametrize('parallel', [False, True])
@pytest.mark.parametrize('triple', [False, True])
def test_multiple(tmpdir, config, local_docs, run, urls, triple, parallel):
    """With two or three versions.

    :param tmpdir: pytest fixture.
    :param config: conftest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param urls: conftest fixture.
    :param bool triple: With three versions (including master) instead of two.
    :param bool parallel: Run sphinx-build with -j option.
    """
    config.overflow = ('-j', '2') if parallel else tuple()
    run(local_docs, ['git', 'tag', 'v1.0.0'])
    run(local_docs, ['git', 'push', 'origin', 'v1.0.0'])
    if triple:
        run(local_docs, ['git', 'tag', 'v1.0.1'])
        run(local_docs, ['git', 'push', 'origin', 'v1.0.1'])

    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))

    # Export (git tags point to same master sha).
    exported_root = tmpdir.ensure_dir('exported_root')
    export(str(local_docs), versions['master']['sha'], str(exported_root.join(versions['master']['sha'])))

    # Run and verify directory.
    destination = tmpdir.ensure_dir('destination')
    build_all(str(exported_root), str(destination), versions)
    actual = sorted(f.relto(destination) for f in destination.visit() if f.check(dir=True))
    expected = [
        '.doctrees',
        '_sources',
        '_static',
        'master',
        'master/.doctrees',
        'master/_sources',
        'master/_static',
        'v1.0.0',
        'v1.0.0/.doctrees',
        'v1.0.0/_sources',
        'v1.0.0/_static',
    ]
    if triple:
        expected.extend([
            'v1.0.1',
            'v1.0.1/.doctrees',
            'v1.0.1/_sources',
            'v1.0.1/_static',
        ])
    assert actual == expected

    # Verify root HTML links.
    expected = [
        '<li><a href="master/contents.html">master</a></li>',
        '<li><a href="v1.0.0/contents.html">v1.0.0</a></li>',
    ]
    if triple:
        expected.append('<li><a href="v1.0.1/contents.html">v1.0.1</a></li>')
    urls(destination.join('contents.html'), expected)

    # Verify master links.
    expected = ['<li><a href="contents.html">master</a></li>', '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>']
    if triple:
        expected.append('<li><a href="../v1.0.1/contents.html">v1.0.1</a></li>')
    urls(destination.join('master', 'contents.html'), expected)

    # Verify v1.0.0 links.
    expected = ['<li><a href="../master/contents.html">master</a></li>', '<li><a href="contents.html">v1.0.0</a></li>']
    if triple:
        expected.append('<li><a href="../v1.0.1/contents.html">v1.0.1</a></li>')
    urls(destination.join('v1.0.0', 'contents.html'), expected)
    if not triple:
        return

    # Verify v1.0.1 links.
    urls(destination.join('v1.0.1', 'contents.html'), [
        '<li><a href="../master/contents.html">master</a></li>',
        '<li><a href="../v1.0.0/contents.html">v1.0.0</a></li>',
        '<li><a href="contents.html">v1.0.1</a></li>',
    ])


@pytest.mark.parametrize('show_banner', [False, True])
def test_banner_branch(tmpdir, banner, config, local_docs, run, show_banner):
    """Test banner messages without tags.

    :param tmpdir: pytest fixture.
    :param banner: conftest fixture.
    :param config: conftest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param bool show_banner: Show the banner.
    """
    run(local_docs, ['git', 'checkout', '-b', 'old_build', 'master'])
    run(local_docs, ['git', 'checkout', 'master'])
    run(local_docs, ['git', 'rm', 'two.rst'])
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
    run(local_docs, ['git', 'push', 'origin', 'master', 'old_build'])

    config.show_banner = show_banner
    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))
    versions['master']['found_docs'] = ('contents', 'one')
    versions['old_build']['found_docs'] = ('contents', 'one', 'two')

    # Export.
    exported_root = tmpdir.ensure_dir('exported_root')
    export(str(local_docs), versions['master']['sha'], str(exported_root.join(versions['master']['sha'])))
    export(str(local_docs), versions['old_build']['sha'], str(exported_root.join(versions['old_build']['sha'])))

    # Run and verify files.
    dst = tmpdir.ensure_dir('destination')
    build_all(str(exported_root), str(dst), versions)
    actual = sorted(f.relto(dst) for f in dst.visit(lambda p: p.basename in ('contents.html', 'one.html', 'two.html')))
    expected = [
        'contents.html', 'master/contents.html', 'master/one.html',
        'old_build/contents.html', 'old_build/one.html', 'old_build/two.html', 'one.html'
    ]
    assert actual == expected

    # Verify no banner.
    if not show_banner:
        for path in expected:
            banner(dst.join(path), None)
        return
    for path in ('contents.html', 'master/contents.html', 'master/one.html', 'one.html'):
        banner(dst.join(path), None)

    # Verify banner.
    banner(dst.join('old_build', 'contents.html'), '../master/contents.html',
           'the development version of Python. The main version is master')
    banner(dst.join('old_build', 'one.html'), '../master/one.html',
           'the development version of Python. The main version is master')
    banner(dst.join('old_build', 'two.html'), '', 'the development version of Python')


@pytest.mark.parametrize('recent', [False, True])
def test_banner_tag(tmpdir, banner, config, local_docs, run, recent):
    """Test banner messages with tags.

    :param tmpdir: pytest fixture.
    :param banner: conftest fixture.
    :param config: conftest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param bool recent: --banner-recent-tag instead of --banner-greatest-tag.
    """
    old, new = ('201611', '201612') if recent else ('v1.0.0', 'v2.0.0')
    run(local_docs, ['git', 'tag', old])
    run(local_docs, ['git', 'mv', 'two.rst', 'too.rst'])
    local_docs.join('contents.rst').write(
        'Test\n'
        '====\n'
        '\n'
        'Sample documentation.\n'
        '\n'
        '.. toctree::\n'
        '    one\n'
        '    too\n'
    )
    local_docs.join('too.rst').write(
        '.. _too:\n'
        '\n'
        'Too\n'
        '===\n'
        '\n'
        'Sub page documentation 2 too.\n'
    )
    run(local_docs, ['git', 'commit', '-am', 'Deleted.'])
    run(local_docs, ['git', 'tag', new])
    run(local_docs, ['git', 'push', 'origin', 'master', old, new])

    config.banner_greatest_tag = not recent
    config.banner_main_ref = new
    config.banner_recent_tag = recent
    config.show_banner = True
    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))
    versions['master']['found_docs'] = ('contents', 'one', 'too')
    versions[new]['found_docs'] = ('contents', 'one', 'too')
    versions[old]['found_docs'] = ('contents', 'one', 'two')

    # Export.
    exported_root = tmpdir.ensure_dir('exported_root')
    export(str(local_docs), versions['master']['sha'], str(exported_root.join(versions['master']['sha'])))
    export(str(local_docs), versions[old]['sha'], str(exported_root.join(versions[old]['sha'])))

    # Run and verify files.
    dst = tmpdir.ensure_dir('destination')
    build_all(str(exported_root), str(dst), versions)
    actual = sorted(f.relto(dst)
                    for f in dst.visit(lambda p: p.basename in ('contents.html', 'one.html', 'two.html', 'too.html')))
    expected = ['contents.html', 'master/contents.html', 'master/one.html', 'master/too.html', 'one.html', 'too.html']
    if recent:
        expected = ['201612/contents.html', '201612/one.html', '201612/too.html'] + expected
        expected = ['201611/contents.html', '201611/one.html', '201611/two.html'] + expected
    else:
        expected += ['v1.0.0/contents.html', 'v1.0.0/one.html', 'v1.0.0/two.html']
        expected += ['v2.0.0/contents.html', 'v2.0.0/one.html', 'v2.0.0/too.html']
    assert actual == expected

    # Verify master banner.
    for page in ('contents', 'one', 'too'):
        banner(dst.join('{}.html'.format(page)), '{new}/{page}.html'.format(new=new, page=page),
               'the development version of Python. The latest version is {}'.format(new))
        banner(dst.join('master', '{}.html'.format(page)), '../{new}/{page}.html'.format(new=new, page=page),
               'the development version of Python. The latest version is {}'.format(new))

    # Verify old tag banner.
    banner(
        dst.join(old, 'contents.html'), '../{}/contents.html'.format(new),
        'an old version of Python. The latest version is {}'.format(new)
    )
    banner(
        dst.join(old, 'one.html'), '../{}/one.html'.format(new),
        'an old version of Python. The latest version is {}'.format(new)
    )
    banner(dst.join(old, 'two.html'), '', 'an old version of Python')


@pytest.mark.parametrize('parallel', [False, True])
def test_error(tmpdir, config, local_docs, run, urls, parallel):
    """Test with a bad root ref. Also test skipping bad non-root refs.

    :param tmpdir: pytest fixture.
    :param config: conftest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param urls: conftest fixture.
    :param bool parallel: Run sphinx-build with -j option.
    """
    config.overflow = ('-j', '2') if parallel else tuple()
    run(local_docs, ['git', 'checkout', '-b', 'a_good', 'master'])
    run(local_docs, ['git', 'checkout', '-b', 'c_good', 'master'])
    run(local_docs, ['git', 'checkout', '-b', 'b_broken', 'master'])
    local_docs.join('conf.py').write('master_doc = exception\n')
    run(local_docs, ['git', 'commit', '-am', 'Broken version.'])
    run(local_docs, ['git', 'checkout', '-b', 'd_broken', 'b_broken'])
    run(local_docs, ['git', 'push', 'origin', 'a_good', 'b_broken', 'c_good', 'd_broken'])

    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))

    exported_root = tmpdir.ensure_dir('exported_root')
    export(str(local_docs), versions['master']['sha'], str(exported_root.join(versions['master']['sha'])))
    export(str(local_docs), versions['b_broken']['sha'], str(exported_root.join(versions['b_broken']['sha'])))

    # Bad root ref.
    config.root_ref = 'b_broken'
    destination = tmpdir.ensure_dir('destination')
    with pytest.raises(HandledError):
        build_all(str(exported_root), str(destination), versions)

    # Remove bad non-root refs.
    config.root_ref = 'master'
    build_all(str(exported_root), str(destination), versions)
    assert [r['name'] for r in versions.remotes] == ['a_good', 'c_good', 'master']

    # Verify root HTML links.
    urls(destination.join('contents.html'), [
        '<li><a href="a_good/contents.html">a_good</a></li>',
        '<li><a href="c_good/contents.html">c_good</a></li>',
        '<li><a href="master/contents.html">master</a></li>',
    ])

    # Verify a_good links.
    urls(destination.join('a_good', 'contents.html'), [
        '<li><a href="contents.html">a_good</a></li>',
        '<li><a href="../c_good/contents.html">c_good</a></li>',
        '<li><a href="../master/contents.html">master</a></li>',
    ])

    # Verify c_good links.
    urls(destination.join('c_good', 'contents.html'), [
        '<li><a href="../a_good/contents.html">a_good</a></li>',
        '<li><a href="contents.html">c_good</a></li>',
        '<li><a href="../master/contents.html">master</a></li>',
    ])

    # Verify master links.
    urls(destination.join('master', 'contents.html'), [
        '<li><a href="../a_good/contents.html">a_good</a></li>',
        '<li><a href="../c_good/contents.html">c_good</a></li>',
        '<li><a href="contents.html">master</a></li>',
    ])


def test_all_errors(tmpdir, local_docs, run, urls):
    """Test good root ref with all bad non-root refs.

    :param tmpdir: pytest fixture.
    :param local_docs: conftest fixture.
    :param run: conftest fixture.
    :param urls: conftest fixture.
    """
    run(local_docs, ['git', 'checkout', '-b', 'a_broken', 'master'])
    local_docs.join('conf.py').write('master_doc = exception\n')
    run(local_docs, ['git', 'commit', '-am', 'Broken version.'])
    run(local_docs, ['git', 'checkout', '-b', 'b_broken', 'a_broken'])
    run(local_docs, ['git', 'push', 'origin', 'a_broken', 'b_broken'])

    versions = Versions(gather_git_info(str(local_docs), ['conf.py'], tuple(), tuple()))

    exported_root = tmpdir.ensure_dir('exported_root')
    export(str(local_docs), versions['master']['sha'], str(exported_root.join(versions['master']['sha'])))
    export(str(local_docs), versions['b_broken']['sha'], str(exported_root.join(versions['b_broken']['sha'])))

    # Run.
    destination = tmpdir.ensure_dir('destination')
    build_all(str(exported_root), str(destination), versions)
    assert [r['name'] for r in versions.remotes] == ['master']

    # Verify root HTML links.
    urls(destination.join('contents.html'), ['<li><a href="master/contents.html">master</a></li>'])
    urls(destination.join('master', 'contents.html'), ['<li><a href="contents.html">master</a></li>'])
