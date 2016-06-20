"""Interface with git locally and remotely."""

import os
import re

from subprocess import CalledProcessError, check_output, STDOUT

RE_REMOTE = re.compile(r'^(?P<sha>[0-9a-f]{5,40})\trefs/(?P<kind>\w+)/(?P<name>[\w./-]+(?:\^\{})?)$', re.MULTILINE)
RE_UNIX_TIME = re.compile(r'^\d{10}$', re.MULTILINE)


class GitError(Exception):
    """Raised if git exits non-zero."""

    def __init__(self, message, output):
        """Constructor."""
        self.message = message
        self.output = output
        super(GitError, self).__init__(message, output)


def chunk(iterator, max_size):
    """Chunk a list/set/etc.

    :param iter iterator: The iterable object to chunk.
    :param int max_size: Max size of each chunk. Remainder chunk may be smaller.

    :return: Yield list of items.
    :rtype: iter
    """
    gen = iter(iterator)
    while True:
        chunked = list()
        for i, item in enumerate(gen):
            chunked.append(item)
            if i >= max_size - 1:
                break
        if not chunked:
            return
        yield chunked


def run_command(local_root, command):
    """check_output() wrapper.

    :param str local_root: Local path to git root directory.
    :param iter command: Command to run.

    :return: Command output.
    :rtype: str
    """
    git_root = os.path.join(local_root, '.git')
    env = dict(os.environ, GIT_DIR=git_root)
    return check_output(command, cwd=local_root, env=env, stderr=STDOUT).decode('utf-8')


def get_root(directory):
    """Get root directory of the local git repo from any subdirectory within it.

    :raise GitError: If git command fails (dir not a git repo?).

    :param str directory: Subdirectory in the local repo.

    :return: Root directory of repository.
    :rtype: str
    """
    env = {k: v for k, v in os.environ.items() if k != 'GIT_DIR'}
    command = ['git', 'rev-parse', '--show-toplevel']
    try:
        output = check_output(command, cwd=directory, env=env, stderr=STDOUT).decode('utf-8')
    except CalledProcessError as exc:
        raise GitError('Git failed to list remote refs.', exc.output.decode('utf-8'))
    return output.strip()


def list_remote(local_root):
    """Get remote branch/tag latest SHAs.

    :raise GitError: When git ls-remote fails.

    :param str local_root: Local path to git root directory.

    :return: List of tuples containing strings. Each tuple is sha, name, kind.
    :rtype: list
    """
    command = ['git', 'ls-remote', '--heads', '--tags']
    try:
        output = run_command(local_root, command)
    except CalledProcessError as exc:
        raise GitError('Git failed to list remote refs.', exc.output.decode('utf-8'))

    # Dereference annotated tags if any. No need to fetch annotations.
    if '^{}' in output:
        parsed = list()
        for group in (m.groupdict() for m in RE_REMOTE.finditer(output)):
            dereferenced, name, kind = group['name'].endswith('^{}'), group['name'][:-3], group['kind']
            if dereferenced and parsed and kind == parsed[-1]['kind'] == 'tags' and name == parsed[-1]['name']:
                parsed[-1]['sha'] = group['sha']
            else:
                parsed.append(group)
    else:
        parsed = [m.groupdict() for m in RE_REMOTE.finditer(output)]

    return [[i['sha'], i['name'], i['kind']] for i in parsed]


def filter_and_date(local_root, conf_rel_path, commits):
    """Get commit Unix timestamps. Exclude commits with no conf.py file.

    :raise CalledProcessError: Unhandled git command failure.
    :raise GitError: A commit SHA has not been fetched.
    :raise ValueError: Unexpected output from git.

    :param str local_root: Local path to git root directory.
    :param str conf_rel_path: Relative path (to git root) of Sphinx conf.py (e.g. docs/conf.py).
    :param iter commits: List of commit SHAs.

    :return: Commit time (seconds since Unix epoch) for each commit. SHA keys and int values.
    :rtype: dict
    """
    dates = dict()

    # Filter without docs.
    for commit in commits:
        if commit in dates:
            continue
        command = ['git', 'ls-tree', '--name-only', '-r', commit, conf_rel_path]
        try:
            output = run_command(local_root, command)
        except CalledProcessError as exc:
            raise GitError('Git ls-tree failed on {0}'.format(commit), exc.output.decode('utf-8'))
        if output:
            dates[commit] = None

    # Get timestamps by groups of 50.
    command_prefix = ['git', 'show', '--no-patch', '--pretty=format:%ct']
    for commits_group in chunk(dates, 50):
        command = command_prefix + commits_group
        output = run_command(local_root, command)
        timestamps = [int(i) for i in RE_UNIX_TIME.findall(output)]
        for i, commit in enumerate(commits_group):
            dates[commit] = timestamps[i]

    # Done.
    return dates


def fetch_commits(local_root, remotes):
    """Fetch from origin.

    :raise CalledProcessError: Unhandled git command failure.

    :param str local_root: Local path to git root directory.
    :param iter remotes: Output of list_remote().
    """
    # Fetch all known branches.
    command = ['git', 'fetch', 'origin']
    run_command(local_root, command)

    # Fetch new branches/tags.
    for sha, name, kind in remotes:
        try:
            run_command(local_root, ['git', 'reflog', sha])
        except CalledProcessError:
            run_command(local_root, command + ['refs/{0}/{1}'.format(kind, name)])
            run_command(local_root, ['git', 'reflog', sha])
