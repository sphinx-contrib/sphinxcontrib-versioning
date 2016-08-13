"""Collect and sort version strings."""

import re

RE_SEMVER = re.compile(r'^v?V?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?([\w.+-]*)$')


def semvers(names):
    """Parse versions into integers and convert non-integer meta indicators into integers with ord().

    Each return list item has an indicator as the first item. 0 for valid versions and 1 for invalid. Can be used to
    sort non-version names (e.g. master, feature_branch, etc) after valid versions. No sorting is done in this function
    though.

    Read multi_sort() docstring for reasoning behind inverted integers in version_ints variable.

    :param iter names: List of strings representing versions/tags/branches.

    :return: List of parsed versions. E.g. v1.10.0b3 -> [0, 1, 10, 0, ord('b'), ord('3')]
    :rtype: list
    """
    matches = [(RE_SEMVER.findall(n) or [[]])[0] for n in names]
    max_len_ints = 0
    max_len_str = 0

    # Get max lens for padding.
    for match in (m for m in matches if m):
        max_len_ints = len(match)  # Never changes.
        max_len_str = max(max_len_str, len(match[-1]))
    if not max_len_ints:
        return matches  # Nothing to do, all empty.
    invalid_template = [1] + [0] * (max_len_ints + max_len_str - 1)

    # Parse.
    exploded_semver = list()
    for match in matches:
        if not match:
            exploded_semver.append(invalid_template[:])
            continue
        version_ints = [-int(i or 0) for i in match[:-1]]
        ints_of_str = [ord(i) for i in match[-1]] + [0] * (max_len_str - len(match[-1]))
        exploded_semver.append([0] + version_ints + ints_of_str)

    return exploded_semver


def multi_sort(remotes, sort):
    """Sort `remotes` in place. Allows sorting by multiple conditions.

    This is needed because Python 3 no longer supports sorting lists of multiple types. Sort keys must all be of the
    same type.

    Problem: the user expects versions to be sorted latest first and timelogical to be most recent first (when viewing
    the HTML documentation), yet expects alphabetical sorting to be A before Z.
    Solution: invert integers (dates and parsed versions).

    :param iter remotes: List of dicts from Versions().remotes.
    :param iter sort: What to sort by. May be one or more of: alpha, time, semver
    """
    exploded_alpha = list()
    exploded_semver = list()

    # Convert name to int if alpha is in sort.
    if 'alpha' in sort:
        alpha_max_len = max(len(r['name']) for r in remotes)
        for name in (r['name'] for r in remotes):
            exploded_alpha.append([ord(i) for i in name] + [0] * (alpha_max_len - len(name)))

    # Parse versions if semver is in sort.
    if 'semver' in sort:
        exploded_semver = semvers(r['name'] for r in remotes)

    # Build sort_mapping dict.
    sort_mapping = dict()
    for i, remote in enumerate(remotes):
        key = list()
        for sort_by in sort:
            if sort_by == 'alpha':
                key.extend(exploded_alpha[i])
            elif sort_by == 'time':
                key.append(-remote['date'])
            elif sort_by == 'semver':
                key.extend(exploded_semver[i])
        sort_mapping[id(remote)] = key

    # Sort.
    remotes.sort(key=lambda k: sort_mapping.get(id(k)))


class Versions(object):
    """Iterable class that holds all versions and handles sorting and filtering. To be fed into Sphinx's Jinja2 env.

    URLs are just '.' initially. Set after instantiation by another function elsewhere. Will be relative URL path.

    :ivar iter remotes: List of dicts for every branch/tag.
    :ivar dict greatest_tag_remote: Tag with the highest version number if it's a valid semver.
    :ivar dict recent_branch_remote: Most recently committed branch.
    :ivar dict recent_remote: Most recently committed branch/tag.
    :ivar dict recent_tag_remote: Most recently committed tag.
    :ivar dict root_remote: Branch/tag at the root of all HTML docs.
    """

    def __init__(self, remotes, sort=None, priority=None, invert=False):
        """Constructor.

        :param iter remotes: Output of routines.gather_git_info(). Converted to list of dicts as instance variable.
        :param iter sort: List of strings (order matters) to sort remotes by. Strings may be: alpha, time, semver
        :param str priority: May be "branches" or "tags". Groups either before the other. Maintains order otherwise.
        :param bool invert: Invert sorted/grouped remotes at the end of processing.
        """
        self.remotes = [dict(
            id='/'.join(r[2:0:-1]),  # str; kind/name
            sha=r[0],  # str
            name=r[1],  # str
            kind=r[2],  # str
            date=r[3],  # int
            conf_rel_path=r[4],  # str
            found_docs=tuple(),  # tuple of str
            url='.',  # str
        ) for r in remotes]
        self.greatest_tag_remote = None
        self.recent_branch_remote = None
        self.recent_remote = None
        self.recent_tag_remote = None
        self.root_remote = None

        # Sort one or more times.
        if sort:
            multi_sort(self.remotes, [s.strip().lower() for s in sort])

        # Priority.
        if priority == 'branches':
            self.remotes.sort(key=lambda r: 1 if r['kind'] == 'tags' else 0)
        elif priority == 'tags':
            self.remotes.sort(key=lambda r: 0 if r['kind'] == 'tags' else 1)

        # Invert.
        if invert:
            self.remotes.reverse()

        # Get significant remotes.
        if self.remotes:
            remotes = self.remotes[:]
            multi_sort(remotes, ('time',))
            self.recent_remote = remotes[0]
            self.recent_branch_remote = ([r for r in remotes if r['kind'] != 'tags'] or [None])[0]
            self.recent_tag_remote = ([r for r in remotes if r['kind'] == 'tags'] or [None])[0]
            if self.recent_tag_remote:
                multi_sort(remotes, ('semver',))
                greatest_tag_remote = [r for r in remotes if r['kind'] == 'tags'][0]
                if RE_SEMVER.search(greatest_tag_remote['name']):
                    self.greatest_tag_remote = greatest_tag_remote

    def __bool__(self):
        """True if self.remotes is not empty. Python 3.x."""
        return bool(self.remotes)

    def __nonzero__(self):
        """True if self.remotes is not empty. Python 2.x."""
        return self.__bool__()

    def __len__(self):
        """Length of self.remotes."""
        return len(self.remotes)

    def __getitem__(self, item):
        """Retrieve a version dict from self.remotes by any of its attributes."""
        # First assume item is an attribute.
        for key in ('id', 'sha', 'name', 'date', 'url'):
            for remote in self.remotes:
                if remote[key] == item:
                    return remote
        # Next assume item is a substring of a sha.
        try:
            length = len(item)
        except TypeError:  # Not an int.
            length = 0
        if length >= 5:
            for remote in self.remotes:
                if item in remote['sha']:
                    return remote
        # Finally assume it's an index. Raises IndexError if item is int.
        try:
            return self.remotes[item]
        except TypeError:
            pass
        # Nothing found, IndexError not raised. item was probably a string, raising KeyError.
        raise KeyError(item)

    def __iter__(self):
        """Yield name and urls of branches and tags."""
        for remote in self.remotes:
            yield remote['name'], remote['url']

    @property
    def branches(self):
        """Return list of (name and urls) only branches."""
        return [(r['name'], r['url']) for r in self.remotes if r['kind'] == 'heads']

    @property
    def tags(self):
        """Return list of (name and urls) only tags."""
        return [(r['name'], r['url']) for r in self.remotes if r['kind'] == 'tags']

    def copy(self, sub_depth=0, pagename=None):
        """Duplicate class and self.remotes dictionaries. Prepend '../' to all URLs n times.

        If current pagename is available in another version, link directly to that page instead of master_doc.

        :param int sub_depth: Subdirectory depth. 1 == ../, 2 == ../../,
        :param str pagename: Name of the page being rendered (without .html or any file extension).

        :return: Versions
        """
        new = self.__class__([])
        for remote_old, remote_new in ((r, r.copy()) for r in self.remotes):
            new.remotes.append(remote_new)

            # Handle sub_depth URL.
            if sub_depth > 0:
                path = '/'.join(['..'] * sub_depth + [remote_new['url']])
                if path.endswith('/.'):
                    path = path[:-2]
                remote_new['url'] = path

            # Handle pagename URL.
            if remote_new['url'].endswith('.html') and pagename in remote_new['found_docs']:
                if '/' in remote_new['url']:
                    remote_new['url'] = '{}/{}.html'.format(remote_new['url'].rsplit('/', 1)[0], pagename)
                else:
                    remote_new['url'] = '{}.html'.format(pagename)

            # Handle pinned remotes.
            if self.greatest_tag_remote == remote_old:
                new.greatest_tag_remote = remote_new
            if self.recent_branch_remote == remote_old:
                new.recent_branch_remote = remote_new
            if self.recent_remote == remote_old:
                new.recent_remote = remote_new
            if self.recent_tag_remote == remote_old:
                new.recent_tag_remote = remote_new
            if self.root_remote == remote_old:
                new.root_remote = remote_new
        return new

    def set_root_remote(self, root_ref):
        """Set the root remote based on the root ref.

        :param str root_ref: Branch/tag at the root of all HTML docs.
        """
        self.root_remote = self[root_ref]
