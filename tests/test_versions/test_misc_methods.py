"""Test methods in Versions class."""

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
@pytest.mark.parametrize('sort', ['alpha', 'time'])
@pytest.mark.parametrize('priority', ['branches', 'tags'])
@pytest.mark.parametrize('invert', [False, True])
def test_priority(remotes, sort, priority, invert):
    """Test with branches/tags being prioritized.

    :param iter remotes: Passed to class.
    :param str sort: Passed to class after splitting by comma.
    :param str priority: Passed to class.
    :param bool invert: Passed to class.
    """
    versions = Versions(remotes, sort=sort.split(','), priority=priority, invert=invert)
    actual = [i[0] for i in versions]

    if sort == 'alpha' and priority == 'branches':
        if invert:
            expected = ['v3.0.0', 'v2.1.0', 'v2.0.0', 'v10.0.0', 'v1.2.0', 'zh-pages', 'master']
        else:
            expected = ['master', 'zh-pages', 'v1.2.0', 'v10.0.0', 'v2.0.0', 'v2.1.0', 'v3.0.0']
    elif sort == 'alpha':
        if invert:
            expected = ['zh-pages', 'master', 'v3.0.0', 'v2.1.0', 'v2.0.0', 'v10.0.0', 'v1.2.0']
        else:
            expected = ['v1.2.0', 'v10.0.0', 'v2.0.0', 'v2.1.0', 'v3.0.0', 'master', 'zh-pages']
    elif sort == 'time' and priority == 'branches':
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
