"""Interface with git locally and remotely."""

import json
import logging
import os
import re
import shutil
from subprocess import CalledProcessError, PIPE, Popen, STDOUT

from sphinxcontrib.versioning.lib import TemporaryDirectory

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


def run_command(local_root, command, env_var=True, piped=None):
    """Run a command and return the output. Run another command and pipe its output to the primary command.

    :raise CalledProcessError: Command exits non-zero.

    :param str local_root: Local path to git root directory.
    :param iter command: Command to run.
    :param bool env_var: Define GIT_DIR environment variable.
    :param iter piped: Second command to pipe its stdout to `command`'s stdin.

    :return: Command output.
    :rtype: str
    """
    log = logging.getLogger(__name__)

    # Setup env.
    env = os.environ.copy()
    if env_var:
        env['GIT_DIR'] = os.path.join(local_root, '.git')
    else:
        env.pop('GIT_DIR', None)

    # Start commands.
    parent = Popen(piped, cwd=local_root, env=env, stdout=PIPE, stderr=PIPE) if piped else None
    main = Popen(command, cwd=local_root, env=env, stdout=PIPE, stderr=STDOUT, stdin=parent.stdout if piped else None)

    # Wait for commands and log.
    common_dict = dict(cwd=local_root, env=env, stdin=None)
    if piped:
        main.wait()  # Let main command read parent.stdout before parent.communicate() does.
        parent_output = parent.communicate()[1].decode('utf-8')
        log.debug(json.dumps(dict(common_dict, command=piped, code=parent.poll(), output=parent_output)))
    else:
        parent_output = ''
    main_output = main.communicate()[0].decode('utf-8')
    log.debug(json.dumps(dict(common_dict, command=command, code=main.poll(), output=main_output, stdin=piped)))

    # Verify success.
    if piped and parent.poll() != 0:
        raise CalledProcessError(parent.poll(), piped, output=parent_output)
    if main.poll() != 0:
        raise CalledProcessError(main.poll(), command, output=main_output)

    return main_output


def get_root(directory):
    """Get root directory of the local git repo from any subdirectory within it.

    :raise GitError: If git command fails (dir not a git repo?).

    :param str directory: Subdirectory in the local repo.

    :return: Root directory of repository.
    :rtype: str
    """
    command = ['git', 'rev-parse', '--show-toplevel']
    try:
        output = run_command(directory, command, env_var=False)
    except CalledProcessError as exc:
        raise GitError('Failed to find local git repository root.', exc.output)
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
        raise GitError('Git failed to list remote refs.', exc.output)

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


def filter_and_date(local_root, conf_rel_paths, commits):
    """Get commit Unix timestamps. Exclude commits with no conf.py file.

    :raise CalledProcessError: Unhandled git command failure.
    :raise GitError: A commit SHA has not been fetched.

    :param str local_root: Local path to git root directory.
    :param iter conf_rel_paths: List of possible relative paths (to git root) of Sphinx conf.py (e.g. docs/conf.py).
    :param iter commits: List of commit SHAs.

    :return: Commit time (seconds since Unix epoch) for each commit. SHA keys and int values.
    :rtype: dict
    """
    dates = dict()

    # Filter without docs.
    for commit in commits:
        if commit in dates:
            continue
        command = ['git', 'ls-tree', '--name-only', '-r', commit] + conf_rel_paths
        try:
            output = run_command(local_root, command)
        except CalledProcessError as exc:
            raise GitError('Git ls-tree failed on {0}'.format(commit), exc.output)
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


def export(local_root, conf_rel_paths, commit, target):
    """Export git commit to directory. "Extracts" all files at the commit to the target directory.

    :raise CalledProcessError: Unhandled git command failure.

    :param str local_root: Local path to git root directory.
    :param iter conf_rel_paths: List of possible relative paths (to git root) of Sphinx conf.py (e.g. docs/conf.py).
    :param str commit: Git commit SHA to export.
    :param str target: Directory to export to.
    """
    docs_rel_paths = [os.path.dirname(p) for p in conf_rel_paths]
    if not all(docs_rel_paths):  # If one path is in the root just extract everything.
        docs_rel_paths = list()
    git_command = ['git', 'archive', '--format=tar', commit] + docs_rel_paths

    with TemporaryDirectory() as temp_dir:
        # Run commands.
        run_command(local_root, ['tar', '-x', '-C', temp_dir], piped=git_command)

        # Determine source.
        source = None
        for path in (os.path.join(temp_dir, c) for c in conf_rel_paths):
            if os.path.exists(path):
                source = os.path.dirname(path)
                break

        # Copy to target. Overwrite existing but don't delete anything in target.
        for s_dirpath, s_filenames in (i[::2] for i in os.walk(source) if i[2]):
            t_dirpath = os.path.join(target, os.path.relpath(s_dirpath, source))
            if not os.path.exists(t_dirpath):
                os.makedirs(t_dirpath)
            for args in ((os.path.join(s_dirpath, f), os.path.join(t_dirpath, f)) for f in s_filenames):
                shutil.copy(*args)
