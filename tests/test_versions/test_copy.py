"""Test method in module."""

from sphinxcontrib.versioning.versions import Versions

REMOTES = (
    ('0772e5ff32af52115a809d97cd506837fa209f7f', 'zh-pages', 'heads', 1465766422, 'README'),
    ('abaaa358379408d997255ec8155db30cea2a61a8', 'master', 'heads', 1465764862, 'README'),
    ('3b7987d8f5f50457f960cfbb04f69b4f1cb3e5ac', 'v1.2.0', 'tags', 1433133463, 'README'),
    ('c4f19d2996ed1ab027b342dd0685157e3572679d', 'v2.0.0', 'tags', 2444613111, 'README'),
    ('936956cca39e93cf727e056bfa631bb92319d197', 'v2.1.0', 'tags', 1446526830, 'README'),
    ('23781ad05995212d3304fa5e97a37540c35f18a2', 'v3.0.0', 'tags', 1464657292, 'README'),
    ('a0db52ded175520aa194e21c4b65b2095ad45358', 'v10.0.0', 'tags', 1464657293, 'README'),
)


def test_copy():
    """Test copy() method."""
    versions = Versions(REMOTES)
    versions['zh-pages']['url'] = 'zh-pages'
    versions['v1.2.0']['url'] = 'v1.2.0'

    # No change in values.
    versions2 = versions.copy()
    assert versions.root_remote is None
    assert versions2.root_remote is None
    assert id(versions) != id(versions2)
    for remote_old, remote_new in ((r, versions2.remotes[i]) for i, r in enumerate(versions.remotes)):
        assert remote_old == remote_new  # Values.
        assert id(remote_old) != id(remote_new)

    # Set root remote.
    versions.set_root_remote('zh-pages')
    versions2 = versions.copy()
    assert versions.root_remote['name'] == 'zh-pages'
    assert versions2.root_remote['name'] == 'zh-pages'
    assert id(versions.root_remote) != id(versions2.root_remote)

    # Depth of one.
    versions2 = versions.copy(1)
    urls = dict()
    assert id(versions) != id(versions2)
    for remote_old, remote_new in ((r, versions2.remotes[i]) for i, r in enumerate(versions.remotes)):
        assert remote_old != remote_new
        assert id(remote_old) != id(remote_new)
        url_old, url_new = remote_old.pop('url'), remote_new.pop('url')
        assert remote_old == remote_new
        remote_old['url'] = url_old
        urls[remote_old['name']] = url_old, url_new
    assert urls['master'] == ('.', '..')
    assert urls['zh-pages'] == ('zh-pages', '../zh-pages')
    assert urls['v1.2.0'] == ('v1.2.0', '../v1.2.0')

    # Depth of two.
    versions2 = versions.copy(2)
    assert versions2['master']['url'] == '../..'
    assert versions2['zh-pages']['url'] == '../../zh-pages'
    assert versions2['v1.2.0']['url'] == '../../v1.2.0'

    # Depth of 20.
    versions2 = versions.copy(20)
    actual = versions2['master']['url']
    expected = '../../../../../../../../../../../../../../../../../../../..'
    assert actual == expected
    actual = versions2['zh-pages']['url']
    expected = '../../../../../../../../../../../../../../../../../../../../zh-pages'
    assert actual == expected
    actual = versions2['v1.2.0']['url']
    expected = '../../../../../../../../../../../../../../../../../../../../v1.2.0'
    assert actual == expected


def test_copy_pagename():
    """Test copy() method with pagename attribute."""
    versions = Versions(REMOTES)
    versions['master']['url'] = 'contents.html'
    versions['master']['found_docs'] = ('contents', 'one', 'two', 'sub/three', 'sub/four')
    versions['zh-pages']['url'] = 'zh-pages/contents.html'
    versions['zh-pages']['found_docs'] = ('contents', 'one', 'sub/three')
    versions['v1.2.0']['url'] = 'v1.2.0/contents.html'
    versions['v1.2.0']['found_docs'] = ('contents', 'one', 'two', 'a', 'sub/three', 'sub/four', 'sub/b')

    # Test from contents doc.
    versions2 = versions.copy(pagename='contents')
    assert versions2['master']['url'] == 'contents.html'
    assert versions2['zh-pages']['url'] == 'zh-pages/contents.html'
    assert versions2['v1.2.0']['url'] == 'v1.2.0/contents.html'
    versions2 = versions.copy(1, pagename='contents')
    assert versions2['master']['url'] == '../contents.html'
    assert versions2['zh-pages']['url'] == '../zh-pages/contents.html'
    assert versions2['v1.2.0']['url'] == '../v1.2.0/contents.html'

    # Test from one doc.
    versions2 = versions.copy(pagename='one')
    assert versions2['master']['url'] == 'one.html'
    assert versions2['zh-pages']['url'] == 'zh-pages/one.html'
    assert versions2['v1.2.0']['url'] == 'v1.2.0/one.html'
    versions2 = versions.copy(1, pagename='one')
    assert versions2['master']['url'] == '../one.html'
    assert versions2['zh-pages']['url'] == '../zh-pages/one.html'
    assert versions2['v1.2.0']['url'] == '../v1.2.0/one.html'

    # Test from two doc.
    versions2 = versions.copy(pagename='two')
    assert versions2['master']['url'] == 'two.html'
    assert versions2['zh-pages']['url'] == 'zh-pages/contents.html'
    assert versions2['v1.2.0']['url'] == 'v1.2.0/two.html'

    # Test from a doc.
    versions2 = versions.copy(pagename='a')
    assert versions2['master']['url'] == 'contents.html'
    assert versions2['zh-pages']['url'] == 'zh-pages/contents.html'
    assert versions2['v1.2.0']['url'] == 'v1.2.0/a.html'

    # Test from sub/three doc.
    versions2 = versions.copy(pagename='sub/three')
    assert versions2['master']['url'] == 'sub/three.html'
    assert versions2['zh-pages']['url'] == 'zh-pages/sub/three.html'
    assert versions2['v1.2.0']['url'] == 'v1.2.0/sub/three.html'

    # Test from sub/four doc.
    versions2 = versions.copy(pagename='sub/four')
    assert versions2['master']['url'] == 'sub/four.html'
    assert versions2['zh-pages']['url'] == 'zh-pages/contents.html'
    assert versions2['v1.2.0']['url'] == 'v1.2.0/sub/four.html'

    # Test from sub/b doc.
    versions2 = versions.copy(pagename='sub/b')
    assert versions2['master']['url'] == 'contents.html'
    assert versions2['zh-pages']['url'] == 'zh-pages/contents.html'
    assert versions2['v1.2.0']['url'] == 'v1.2.0/sub/b.html'
