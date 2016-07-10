"""Test objects in module."""

import pytest

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
REMOTES_SHIFTED = tuple(REMOTES[-s:] + REMOTES[:-s] for s in range(6))


@pytest.mark.parametrize('remotes', REMOTES_SHIFTED)
def test_no_sort(remotes):
    """Test without sorting.

    :param iter remotes: Passed to class.
    """
    versions = Versions(remotes)
    actual_all = [i for i in versions]
    actual_branches = [i for i in versions.branches]
    actual_tags = [i for i in versions.tags]

    expected_all = [(r[1], '.') for r in remotes]
    expected_branches = [(r[1], '.') for r in remotes if r[2] == 'heads']
    expected_tags = [(r[1], '.') for r in remotes if r[2] == 'tags']

    assert actual_all == expected_all
    assert actual_branches == expected_branches
    assert actual_tags == expected_tags


@pytest.mark.parametrize('sort', ['', 'alpha', 'chrono', 'semver', 'semver,alpha', 'semver,chrono'])
def test_sort_valid(sort):
    """Test sorting logic with valid versions (lifted from 2.7 distutils/version.py:LooseVersion.__doc__).

    :param str sort: Passed to function after splitting by comma.
    """
    items = ['v1.5.1', 'V1.5.1b2', '161', '3.10a', '8.02', '3.4j', '1996.07.12', '3.2.pl0', '3.1.1.6', '2g6', '11g',
             '0.960923', '2.2beta29', '1.13++', '5.5.kw', '2.0b1pl0', 'master', 'gh-pages', 'a', 'z']
    remotes = [('', item, 'tags', i, 'README') for i, item in enumerate(items)]
    versions = Versions(remotes, sort=sort.split(','))
    actual = [i[0] for i in versions]

    if sort == 'alpha':
        expected = ['0.960923', '1.13++', '11g', '161', '1996.07.12', '2.0b1pl0', '2.2beta29', '2g6', '3.1.1.6',
                    '3.10a', '3.2.pl0', '3.4j', '5.5.kw', '8.02', 'V1.5.1b2', 'a', 'gh-pages', 'master', 'v1.5.1', 'z']
    elif sort == 'chrono':
        expected = list(reversed(items))
    elif sort == 'semver':
        expected = ['1996.07.12', '161', '11g', '8.02', '5.5.kw', '3.10a', '3.4j', '3.2.pl0', '3.1.1.6', '2.2beta29',
                    '2.0b1pl0', '2g6', '1.13++', 'v1.5.1', 'V1.5.1b2', '0.960923', 'master', 'gh-pages', 'a', 'z']
    elif sort == 'semver,alpha':
        expected = ['1996.07.12', '161', '11g', '8.02', '5.5.kw', '3.10a', '3.4j', '3.2.pl0', '3.1.1.6', '2.2beta29',
                    '2.0b1pl0', '2g6', '1.13++', 'v1.5.1', 'V1.5.1b2', '0.960923', 'a', 'gh-pages', 'master', 'z']
    elif sort == 'semver,chrono':
        expected = ['1996.07.12', '161', '11g', '8.02', '5.5.kw', '3.10a', '3.4j', '3.2.pl0', '3.1.1.6', '2.2beta29',
                    '2.0b1pl0', '2g6', '1.13++', 'v1.5.1', 'V1.5.1b2', '0.960923', 'z', 'a', 'gh-pages', 'master']
    else:
        expected = items

    assert actual == expected


@pytest.mark.parametrize('sort', ['', 'alpha', 'chrono', 'semver', 'semver,alpha', 'semver,chrono'])
def test_sort_semver_invalid(sort):
    """Test sorting logic with nothing but invalid versions.

    :param str sort: Passed to function after splitting by comma.
    """
    items = ['master', 'gh-pages', 'a', 'z']
    remotes = [('', item, 'tags', i, 'README') for i, item in enumerate(items)]
    versions = Versions(remotes, sort=sort.split(','))
    actual = [i[0] for i in versions]

    if sort == 'alpha':
        expected = ['a', 'gh-pages', 'master', 'z']
    elif sort == 'chrono':
        expected = list(reversed(items))
    elif sort == 'semver':
        expected = ['master', 'gh-pages', 'a', 'z']
    elif sort == 'semver,alpha':
        expected = ['a', 'gh-pages', 'master', 'z']
    elif sort == 'semver,chrono':
        expected = ['z', 'a', 'gh-pages', 'master']
    else:
        expected = items

    assert actual == expected


@pytest.mark.parametrize('remotes', REMOTES_SHIFTED)
@pytest.mark.parametrize('sort', ['alpha', 'chrono', 'semver', 'semver,alpha', 'semver,chrono', 'invalid', ''])
def test_sort(remotes, sort):
    """Test with sorting.

    :param iter remotes: Passed to class.
    :param str sort: Passed to class after splitting by comma.
    """
    versions = Versions(remotes, sort=sort.split(','))
    actual = [i[0] for i in versions]

    if sort == 'alpha':
        expected = ['master', 'v1.2.0', 'v10.0.0', 'v2.0.0', 'v2.1.0', 'v3.0.0', 'zh-pages']
    elif sort == 'chrono':
        expected = ['v2.0.0', 'zh-pages', 'master', 'v10.0.0', 'v3.0.0', 'v2.1.0', 'v1.2.0']
    elif sort == 'semver':
        expected = ['v10.0.0', 'v3.0.0', 'v2.1.0', 'v2.0.0', 'v1.2.0', 'zh-pages', 'master']
    elif sort == 'semver,alpha':
        expected = ['v10.0.0', 'v3.0.0', 'v2.1.0', 'v2.0.0', 'v1.2.0', 'master', 'zh-pages']
    elif sort == 'semver,chrono':
        expected = ['v10.0.0', 'v3.0.0', 'v2.1.0', 'v2.0.0', 'v1.2.0', 'zh-pages', 'master']
    else:
        expected = [i[1] for i in remotes]

    assert actual == expected


@pytest.mark.parametrize('remotes', REMOTES_SHIFTED)
@pytest.mark.parametrize('sort', ['alpha', 'chrono'])
@pytest.mark.parametrize('prioritize', ['branches', 'tags'])
@pytest.mark.parametrize('invert', [False, True])
def test_priority(remotes, sort, prioritize, invert):
    """Test with branches/tags being prioritized.

    :param iter remotes: Passed to class.
    :param str sort: Passed to class after splitting by comma.
    :param str prioritize: Passed to class.
    :param bool invert: Passed to class.
    """
    versions = Versions(remotes, sort=sort.split(','), prioritize=prioritize, invert=invert)
    actual = [i[0] for i in versions]

    if sort == 'alpha' and prioritize == 'branches':
        if invert:
            expected = ['v3.0.0', 'v2.1.0', 'v2.0.0', 'v10.0.0', 'v1.2.0', 'zh-pages', 'master']
        else:
            expected = ['master', 'zh-pages', 'v1.2.0', 'v10.0.0', 'v2.0.0', 'v2.1.0', 'v3.0.0']
    elif sort == 'alpha':
        if invert:
            expected = ['zh-pages', 'master', 'v3.0.0', 'v2.1.0', 'v2.0.0', 'v10.0.0', 'v1.2.0']
        else:
            expected = ['v1.2.0', 'v10.0.0', 'v2.0.0', 'v2.1.0', 'v3.0.0', 'master', 'zh-pages']
    elif sort == 'chrono' and prioritize == 'branches':
        if invert:
            expected = ['v1.2.0', 'v2.1.0', 'v3.0.0', 'v10.0.0', 'v2.0.0', 'master', 'zh-pages']
        else:
            expected = ['zh-pages', 'master', 'v2.0.0', 'v10.0.0', 'v3.0.0', 'v2.1.0', 'v1.2.0']
    else:
        if invert:
            expected = ['master', 'zh-pages', 'v1.2.0', 'v2.1.0', 'v3.0.0', 'v10.0.0', 'v2.0.0']
        else:
            expected = ['v2.0.0', 'v10.0.0', 'v3.0.0', 'v2.1.0', 'v1.2.0', 'zh-pages', 'master']

    assert actual == expected


def test_getitem():
    """Test Versions.__getitem__ with integer and string keys/indices."""
    versions = Versions(REMOTES)

    # Test SHA.
    assert versions['0772e5ff32af52115a809d97cd506837fa209f7f']['name'] == 'zh-pages'
    assert versions['abaaa358379408d99725']['name'] == 'master'
    assert versions['3b7987d8f']['name'] == 'v1.2.0'
    assert versions['c4f19']['name'] == 'v2.0.0'

    # Test name and date.
    for name, date in (r[1::2] for r in REMOTES):
        assert versions[name]['name'] == name
        assert versions[date]['name'] == name

    # Set and test URLs.
    versions.remotes[1]['url'] = 'url1'
    versions.remotes[2]['url'] = 'url2'
    versions.remotes[3]['url'] = 'url3'
    assert versions['.']['name'] == 'zh-pages'
    assert versions['url1']['name'] == 'master'
    assert versions['url2']['name'] == 'v1.2.0'
    assert versions['url3']['name'] == 'v2.0.0'

    # Indexes.
    for i, name in enumerate(r[1] for r in REMOTES):
        assert versions[i]['name'] == name

    # Test IndexError.
    with pytest.raises(IndexError):
        assert versions[100]

    # Test KeyError.
    with pytest.raises(KeyError):
        assert versions['unknown']


def test_bool_len():
    """Test length and boolean values of Versions and .branches/.tags."""
    versions = Versions(REMOTES)
    assert bool(versions) is True
    assert bool(versions.branches) is True
    assert bool(versions.tags) is True
    assert len(versions) == 7

    versions = Versions(r for r in REMOTES if r[2] == 'heads')
    assert bool(versions) is True
    assert bool(versions.branches) is True
    assert bool(versions.tags) is False
    assert len(versions) == 2

    versions = Versions(r for r in REMOTES if r[2] == 'tags')
    assert bool(versions) is True
    assert bool(versions.branches) is False
    assert bool(versions.tags) is True
    assert len(versions) == 5

    versions = Versions([])
    assert bool(versions) is False
    assert bool(versions.branches) is False
    assert bool(versions.tags) is False
    assert len(versions) == 0


def test_id():
    """Test remote IDs."""
    versions = Versions(REMOTES)
    for remote in versions.remotes:
        assert remote['id'] == '{}/{}'.format(remote['kind'], remote['name'])


def test_copy():
    """Test copy() method."""
    versions = Versions(REMOTES)
    versions['zh-pages']['url'] = 'zh-pages'
    versions['v1.2.0']['url'] = 'v1.2.0'

    # No change in values.
    versions2 = versions.copy()
    assert id(versions) != id(versions2)
    for remote_old, remote_new in ((r, versions2.remotes[i]) for i, r in enumerate(versions.remotes)):
        assert remote_old == remote_new  # Values.
        assert id(remote_old) != id(remote_new)

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
