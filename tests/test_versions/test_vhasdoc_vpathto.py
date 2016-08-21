"""Test methods in Versions class."""

from sphinxcontrib.versioning.versions import Versions


def get_versions(context):
    """Create Versions class instance for tests.

    :param dict context: Update context with this.
    """
    versions = Versions([i * 5, i, 'heads', 1465766422, 'README'] for i in ('a', 'b', 'c'))
    versions.context.update(context)

    versions['a']['found_docs'] = ('contents', '1', 'sub/2', 'sub/sub/3', 'sub/sub/sub/4')

    versions['b']['found_docs'] = ('contents', '1', 'sub/2', 'sub/sub/3', 'sub/sub/sub/4')
    versions['b']['master_doc'] = 'contents'
    versions['b']['root_dir'] = 'b'

    versions['c']['found_docs'] = ('contents', 'A', 'sub/B', 'sub/sub/C', 'sub/sub/sub/D')
    versions['c']['master_doc'] = 'contents'
    versions['c']['root_dir'] = 'c_'

    return versions


def test_root_ref():
    """Test from root ref."""
    versions = get_versions(dict(current_version='a', scv_is_root_ref=True))

    # From contents page. All versions have this page.
    versions.context['pagename'] = 'contents'
    assert versions.vhasdoc('a') is True
    assert versions.vpathto('a') == 'a/contents.html'
    assert versions.vhasdoc('b') is True
    assert versions.vpathto('b') == 'b/contents.html'
    assert versions.vhasdoc('c') is True
    assert versions.vpathto('c') == 'c_/contents.html'
    pairs = list(versions)
    assert pairs == [('a', 'a/contents.html'), ('b', 'b/contents.html'), ('c', 'c_/contents.html')]

    # From 1 page.
    versions.context['pagename'] = '1'
    assert versions.vhasdoc('a') is True
    assert versions.vpathto('a') == 'a/1.html'
    assert versions.vhasdoc('b') is True
    assert versions.vpathto('b') == 'b/1.html'
    assert versions.vhasdoc('c') is False
    assert versions.vpathto('c') == 'c_/contents.html'
    pairs = list(versions)
    assert pairs == [('a', 'a/1.html'), ('b', 'b/1.html'), ('c', 'c_/contents.html')]

    # From sub/2 page.
    versions.context['pagename'] = 'sub/2'
    assert versions.vhasdoc('a') is True
    assert versions.vpathto('a') == '../a/sub/2.html'
    assert versions.vhasdoc('b') is True
    assert versions.vpathto('b') == '../b/sub/2.html'
    assert versions.vhasdoc('c') is False
    assert versions.vpathto('c') == '../c_/contents.html'
    pairs = list(versions)
    assert pairs == [('a', '../a/sub/2.html'), ('b', '../b/sub/2.html'), ('c', '../c_/contents.html')]

    # From sub/sub/3 page.
    versions.context['pagename'] = 'sub/sub/3'
    assert versions.vhasdoc('a') is True
    assert versions.vpathto('a') == '../../a/sub/sub/3.html'
    assert versions.vhasdoc('b') is True
    assert versions.vpathto('b') == '../../b/sub/sub/3.html'
    assert versions.vhasdoc('c') is False
    assert versions.vpathto('c') == '../../c_/contents.html'
    pairs = list(versions)
    assert pairs == [('a', '../../a/sub/sub/3.html'), ('b', '../../b/sub/sub/3.html'), ('c', '../../c_/contents.html')]

    # From sub/sub/sub/4 page.
    versions.context['pagename'] = 'sub/sub/sub/4'
    assert versions.vhasdoc('a') is True
    assert versions.vpathto('a') == '../../../a/sub/sub/sub/4.html'
    assert versions.vhasdoc('b') is True
    assert versions.vpathto('b') == '../../../b/sub/sub/sub/4.html'
    assert versions.vhasdoc('c') is False
    assert versions.vpathto('c') == '../../../c_/contents.html'
    pairs = list(versions)
    assert pairs == [
        ('a', '../../../a/sub/sub/sub/4.html'),
        ('b', '../../../b/sub/sub/sub/4.html'),
        ('c', '../../../c_/contents.html'),
    ]


def test_b():
    """Test version 'b'."""
    versions = get_versions(dict(current_version='b', scv_is_root_ref=False))

    versions.context['pagename'] = 'contents'
    assert versions.vhasdoc('a') is True
    assert versions.vpathto('a') == '../a/contents.html'
    assert versions.vhasdoc('b') is True
    assert versions.vpathto('b') == 'contents.html'
    assert versions.vhasdoc('c') is True
    assert versions.vpathto('c') == '../c_/contents.html'
    pairs = list(versions)
    assert pairs == [('a', '../a/contents.html'), ('b', 'contents.html'), ('c', '../c_/contents.html')]

    versions.context['pagename'] = '1'
    assert versions.vhasdoc('a') is True
    assert versions.vpathto('a') == '../a/1.html'
    assert versions.vhasdoc('b') is True
    assert versions.vpathto('b') == '1.html'
    assert versions.vhasdoc('c') is False
    assert versions.vpathto('c') == '../c_/contents.html'
    pairs = list(versions)
    assert pairs == [('a', '../a/1.html'), ('b', '1.html'), ('c', '../c_/contents.html')]

    versions.context['pagename'] = 'sub/2'
    assert versions.vhasdoc('a') is True
    assert versions.vpathto('a') == '../../a/sub/2.html'
    assert versions.vhasdoc('b') is True
    assert versions.vpathto('b') == '2.html'
    assert versions.vhasdoc('c') is False
    assert versions.vpathto('c') == '../../c_/contents.html'
    pairs = list(versions)
    assert pairs == [('a', '../../a/sub/2.html'), ('b', '2.html'), ('c', '../../c_/contents.html')]

    versions.context['pagename'] = 'sub/sub/3'
    assert versions.vhasdoc('a') is True
    assert versions.vpathto('a') == '../../../a/sub/sub/3.html'
    assert versions.vhasdoc('b') is True
    assert versions.vpathto('b') == '3.html'
    assert versions.vhasdoc('c') is False
    assert versions.vpathto('c') == '../../../c_/contents.html'
    pairs = list(versions)
    assert pairs == [('a', '../../../a/sub/sub/3.html'), ('b', '3.html'), ('c', '../../../c_/contents.html')]

    versions.context['pagename'] = 'sub/sub/sub/4'
    assert versions.vhasdoc('a') is True
    assert versions.vpathto('a') == '../../../../a/sub/sub/sub/4.html'
    assert versions.vhasdoc('b') is True
    assert versions.vpathto('b') == '4.html'
    assert versions.vhasdoc('c') is False
    assert versions.vpathto('c') == '../../../../c_/contents.html'
    pairs = list(versions)
    assert pairs == [('a', '../../../../a/sub/sub/sub/4.html'), ('b', '4.html'), ('c', '../../../../c_/contents.html')]


def test_c():
    """Test version 'c'."""
    versions = get_versions(dict(current_version='c', scv_is_root_ref=False))

    versions.context['pagename'] = 'contents'
    assert versions.vhasdoc('a') is True
    assert versions.vpathto('a') == '../a/contents.html'
    assert versions.vhasdoc('b') is True
    assert versions.vpathto('b') == '../b/contents.html'
    assert versions.vhasdoc('c') is True
    assert versions.vpathto('c') == 'contents.html'
    pairs = list(versions)
    assert pairs == [('a', '../a/contents.html'), ('b', '../b/contents.html'), ('c', 'contents.html')]

    versions.context['pagename'] = 'A'
    assert versions.vhasdoc('a') is False
    assert versions.vpathto('a') == '../a/contents.html'
    assert versions.vhasdoc('b') is False
    assert versions.vpathto('b') == '../b/contents.html'
    assert versions.vhasdoc('c') is True
    assert versions.vpathto('c') == 'A.html'
    pairs = list(versions)
    assert pairs == [('a', '../a/contents.html'), ('b', '../b/contents.html'), ('c', 'A.html')]

    versions.context['pagename'] = 'sub/B'
    assert versions.vhasdoc('a') is False
    assert versions.vpathto('a') == '../../a/contents.html'
    assert versions.vhasdoc('b') is False
    assert versions.vpathto('b') == '../../b/contents.html'
    assert versions.vhasdoc('c') is True
    assert versions.vpathto('c') == 'B.html'
    pairs = list(versions)
    assert pairs == [('a', '../../a/contents.html'), ('b', '../../b/contents.html'), ('c', 'B.html')]

    versions.context['pagename'] = 'sub/sub/C'
    assert versions.vhasdoc('a') is False
    assert versions.vpathto('a') == '../../../a/contents.html'
    assert versions.vhasdoc('b') is False
    assert versions.vpathto('b') == '../../../b/contents.html'
    assert versions.vhasdoc('c') is True
    assert versions.vpathto('c') == 'C.html'
    pairs = list(versions)
    assert pairs == [('a', '../../../a/contents.html'), ('b', '../../../b/contents.html'), ('c', 'C.html')]

    versions.context['pagename'] = 'sub/sub/sub/D'
    assert versions.vhasdoc('a') is False
    assert versions.vpathto('a') == '../../../../a/contents.html'
    assert versions.vhasdoc('b') is False
    assert versions.vpathto('b') == '../../../../b/contents.html'
    assert versions.vhasdoc('c') is True
    assert versions.vpathto('c') == 'D.html'
    pairs = list(versions)
    assert pairs == [('a', '../../../../a/contents.html'), ('b', '../../../../b/contents.html'), ('c', 'D.html')]
