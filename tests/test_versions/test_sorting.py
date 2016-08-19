"""Test sorting versions."""

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
    versions.context.update(dict(pagename='contents', scv_is_root_ref=False, current_version='other'))
    actual_all = [i for i in versions]
    actual_branches = [i for i in versions.branches]
    actual_tags = [i for i in versions.tags]

    expected_all = [(r[1], '../{}/contents.html'.format(r[1])) for r in remotes]
    expected_branches = [(r[1], '../{}/contents.html'.format(r[1])) for r in remotes if r[2] == 'heads']
    expected_tags = [(r[1], '../{}/contents.html'.format(r[1])) for r in remotes if r[2] == 'tags']

    assert actual_all == expected_all
    assert actual_branches == expected_branches
    assert actual_tags == expected_tags
    assert versions.greatest_tag_remote == versions['v10.0.0']
    assert versions.recent_branch_remote == versions['zh-pages']
    assert versions.recent_remote == versions['v2.0.0']
    assert versions.recent_tag_remote == versions['v2.0.0']


@pytest.mark.parametrize('sort', ['', 'alpha', 'time', 'semver', 'semver,alpha', 'semver,time'])
def test_sort_valid(sort):
    """Test sorting logic with valid versions (lifted from 2.7 distutils/version.py:LooseVersion.__doc__).

    :param str sort: Passed to function after splitting by comma.
    """
    items = ['v1.5.1', 'V1.5.1b2', '161', '3.10a', '8.02', '3.4j', '1996.07.12', '3.2.pl0', '3.1.1.6', '2g6', '11g',
             '0.960923', '2.2beta29', '1.13++', '5.5.kw', '2.0b1pl0', 'master', 'gh-pages', 'a', 'z']
    remotes = [('', item, 'tags', i, 'README') for i, item in enumerate(items)]
    versions = Versions(remotes, sort=sort.split(','))
    versions.context.update(dict(pagename='contents', scv_is_root_ref=True, current_version='master'))
    actual = [i[0] for i in versions]

    if sort == 'alpha':
        expected = ['0.960923', '1.13++', '11g', '161', '1996.07.12', '2.0b1pl0', '2.2beta29', '2g6', '3.1.1.6',
                    '3.10a', '3.2.pl0', '3.4j', '5.5.kw', '8.02', 'V1.5.1b2', 'a', 'gh-pages', 'master', 'v1.5.1', 'z']
    elif sort == 'time':
        expected = list(reversed(items))
    elif sort == 'semver':
        expected = ['1996.07.12', '161', '11g', '8.02', '5.5.kw', '3.10a', '3.4j', '3.2.pl0', '3.1.1.6', '2.2beta29',
                    '2.0b1pl0', '2g6', '1.13++', 'v1.5.1', 'V1.5.1b2', '0.960923', 'master', 'gh-pages', 'a', 'z']
    elif sort == 'semver,alpha':
        expected = ['1996.07.12', '161', '11g', '8.02', '5.5.kw', '3.10a', '3.4j', '3.2.pl0', '3.1.1.6', '2.2beta29',
                    '2.0b1pl0', '2g6', '1.13++', 'v1.5.1', 'V1.5.1b2', '0.960923', 'a', 'gh-pages', 'master', 'z']
    elif sort == 'semver,time':
        expected = ['1996.07.12', '161', '11g', '8.02', '5.5.kw', '3.10a', '3.4j', '3.2.pl0', '3.1.1.6', '2.2beta29',
                    '2.0b1pl0', '2g6', '1.13++', 'v1.5.1', 'V1.5.1b2', '0.960923', 'z', 'a', 'gh-pages', 'master']
    else:
        expected = items

    assert actual == expected


@pytest.mark.parametrize('sort', ['', 'alpha', 'time', 'semver', 'semver,alpha', 'semver,time'])
def test_sort_semver_invalid(sort):
    """Test sorting logic with nothing but invalid versions.

    :param str sort: Passed to function after splitting by comma.
    """
    items = ['master', 'gh-pages', 'a', 'z']
    remotes = [('', item, 'tags', i, 'README') for i, item in enumerate(items)]
    versions = Versions(remotes, sort=sort.split(','))
    versions.context.update(dict(pagename='contents', scv_is_root_ref=True, current_version='master'))
    actual = [i[0] for i in versions]

    if sort == 'alpha':
        expected = ['a', 'gh-pages', 'master', 'z']
    elif sort == 'time':
        expected = list(reversed(items))
    elif sort == 'semver':
        expected = ['master', 'gh-pages', 'a', 'z']
    elif sort == 'semver,alpha':
        expected = ['a', 'gh-pages', 'master', 'z']
    elif sort == 'semver,time':
        expected = ['z', 'a', 'gh-pages', 'master']
    else:
        expected = items

    assert actual == expected


@pytest.mark.parametrize('remotes', REMOTES_SHIFTED)
@pytest.mark.parametrize('sort', ['alpha', 'time', 'semver', 'semver,alpha', 'semver,time', 'invalid', ''])
def test_sort(remotes, sort):
    """Test with sorting.

    :param iter remotes: Passed to class.
    :param str sort: Passed to class after splitting by comma.
    """
    versions = Versions(remotes, sort=sort.split(','))
    versions.context.update(dict(pagename='contents', scv_is_root_ref=True, current_version='master'))
    actual = [i[0] for i in versions]

    if sort == 'alpha':
        expected = ['master', 'v1.2.0', 'v10.0.0', 'v2.0.0', 'v2.1.0', 'v3.0.0', 'zh-pages']
    elif sort == 'time':
        expected = ['v2.0.0', 'zh-pages', 'master', 'v10.0.0', 'v3.0.0', 'v2.1.0', 'v1.2.0']
    elif sort == 'semver':
        expected = ['v10.0.0', 'v3.0.0', 'v2.1.0', 'v2.0.0', 'v1.2.0', 'zh-pages', 'master']
    elif sort == 'semver,alpha':
        expected = ['v10.0.0', 'v3.0.0', 'v2.1.0', 'v2.0.0', 'v1.2.0', 'master', 'zh-pages']
    elif sort == 'semver,time':
        expected = ['v10.0.0', 'v3.0.0', 'v2.1.0', 'v2.0.0', 'v1.2.0', 'zh-pages', 'master']
    else:
        expected = [i[1] for i in remotes]

    assert actual == expected
