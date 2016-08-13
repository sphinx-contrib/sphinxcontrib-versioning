"""Interface with git locally and remotely."""

import glob
import json
import logging
import os
import re
import shutil
from datetime import datetime
from subprocess import CalledProcessError, PIPE, Popen, STDOUT

from sphinxcontrib.versioning.lib import TempDir

RE_REMOTE = re.compile(r'^(?P<sha>[0-9a-f]{5,40})\trefs/(?P<kind>heads|tags)/(?P<name>[\w./-]+(?:\^\{})?)$',
                       re.MULTILINE)
RE_UNIX_TIME = re.compile(r'^\d{10}$', re.MULTILINE)
WHITELIST_ENV_VARS = (
    'APPVEYOR',
    'APPVEYOR_ACCOUNT_NAME',
    'APPVEYOR_BUILD_ID',
    'APPVEYOR_BUILD_NUMBER',
    'APPVEYOR_BUILD_VERSION',
    'APPVEYOR_FORCED_BUILD',
    'APPVEYOR_JOB_ID',
    'APPVEYOR_JOB_NAME',
    'APPVEYOR_PROJECT_ID',
    'APPVEYOR_PROJECT_NAME',
    'APPVEYOR_PROJECT_SLUG',
    'APPVEYOR_PULL_REQUEST_NUMBER',
    'APPVEYOR_PULL_REQUEST_TITLE',
    'APPVEYOR_RE_BUILD',
    'APPVEYOR_REPO_BRANCH',
    'APPVEYOR_REPO_COMMIT',
    'APPVEYOR_REPO_NAME',
    'APPVEYOR_REPO_PROVIDER',
    'APPVEYOR_REPO_TAG',
    'APPVEYOR_REPO_TAG_NAME',
    'APPVEYOR_SCHEDULED_BUILD',
    'CI',
    'CI_PULL_REQUEST',
    'CI_PULL_REQUESTS',
    'CIRCLE_BRANCH',
    'CIRCLE_BUILD_IMAGE',
    'CIRCLE_BUILD_NUM',
    'CIRCLE_BUILD_URL',
    'CIRCLE_COMPARE_URL',
    'CIRCLE_PR_NUMBER',
    'CIRCLE_PR_REPONAME',
    'CIRCLE_PR_USERNAME',
    'CIRCLE_PREVIOUS_BUILD_NUM',
    'CIRCLE_PROJECT_REPONAME',
    'CIRCLE_PROJECT_USERNAME',
    'CIRCLE_REPOSITORY_URL',
    'CIRCLE_SHA1',
    'CIRCLE_TAG',
    'CIRCLE_USERNAME',
    'CIRCLECI',
    'HOSTNAME',
    'LANG',
    'LC_ALL',
    'PLATFORM',
    'TRAVIS',
    'TRAVIS_BRANCH',
    'TRAVIS_BUILD_ID',
    'TRAVIS_BUILD_NUMBER',
    'TRAVIS_COMMIT',
    'TRAVIS_COMMIT_RANGE',
    'TRAVIS_EVENT_TYPE',
    'TRAVIS_JOB_ID',
    'TRAVIS_JOB_NUMBER',
    'TRAVIS_OS_NAME',
    'TRAVIS_PULL_REQUEST',
    'TRAVIS_PYTHON_VERSION',
    'TRAVIS_REPO_SLUG',
    'TRAVIS_SECURE_ENV_VARS',
    'TRAVIS_TAG',
    'TRAVIS_TEST_RESULT',
    'USER',
)


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
    with open(os.devnull) as null:
        parent = Popen(piped, cwd=local_root, env=env, stdout=PIPE, stderr=PIPE, stdin=null) if piped else None
        stdin = parent.stdout if piped else null
        main = Popen(command, cwd=local_root, env=env, stdout=PIPE, stderr=STDOUT, stdin=stdin)

    # Wait for commands and log.
    common_dict = dict(cwd=local_root, stdin=None)
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
        raise GitError('Failed to find local git repository root in {}.'.format(repr(directory)), exc.output)
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
    """Get commit Unix timestamps and first matching conf.py path. Exclude commits with no conf.py file.

    :raise CalledProcessError: Unhandled git command failure.
    :raise GitError: A commit SHA has not been fetched.

    :param str local_root: Local path to git root directory.
    :param iter conf_rel_paths: List of possible relative paths (to git root) of Sphinx conf.py (e.g. docs/conf.py).
    :param iter commits: List of commit SHAs.

    :return: Commit time (seconds since Unix epoch) for each commit and conf.py path. SHA keys and [int, str] values.
    :rtype: dict
    """
    dates_paths = dict()

    # Filter without docs.
    for commit in commits:
        if commit in dates_paths:
            continue
        command = ['git', 'ls-tree', '--name-only', '-r', commit] + conf_rel_paths
        try:
            output = run_command(local_root, command)
        except CalledProcessError as exc:
            raise GitError('Git ls-tree failed on {0}'.format(commit), exc.output)
        if output:
            dates_paths[commit] = [None, output.splitlines()[0].strip()]

    # Get timestamps by groups of 50.
    command_prefix = ['git', 'show', '--no-patch', '--pretty=format:%ct']
    for commits_group in chunk(dates_paths, 50):
        command = command_prefix + commits_group
        output = run_command(local_root, command)
        timestamps = [int(i) for i in RE_UNIX_TIME.findall(output)]
        for i, commit in enumerate(commits_group):
            dates_paths[commit][0] = timestamps[i]

    # Done.
    return dates_paths


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


def export(local_root, commit, target):
    """Export git commit to directory. "Extracts" all files at the commit to the target directory.

    :raise CalledProcessError: Unhandled git command failure.

    :param str local_root: Local path to git root directory.
    :param str commit: Git commit SHA to export.
    :param str target: Directory to export to.
    """
    git_command = ['git', 'archive', '--format=tar', commit]

    with TempDir() as temp_dir:
        # Run commands.
        run_command(local_root, ['tar', '-x', '-C', temp_dir], piped=git_command)

        # Copy to target. Overwrite existing but don't delete anything in target.
        for s_dirpath, s_filenames in (i[::2] for i in os.walk(temp_dir) if i[2]):
            t_dirpath = os.path.join(target, os.path.relpath(s_dirpath, temp_dir))
            if not os.path.exists(t_dirpath):
                os.makedirs(t_dirpath)
            for args in ((os.path.join(s_dirpath, f), os.path.join(t_dirpath, f)) for f in s_filenames):
                shutil.copy(*args)


def clone(local_root, new_root, branch, rel_dest, exclude):
    """Clone "local_root" origin into a new directory and check out a specific branch. Optionally run "git rm".

    :raise CalledProcessError: Unhandled git command failure.
    :raise GitError: Handled git failures.

    :param str local_root: Local path to git root directory.
    :param str new_root: Local path empty directory in which branch will be cloned into.
    :param str branch: Checkout this branch.
    :param str rel_dest: Run "git rm" on this directory if exclude is truthy.
    :param iter exclude: List of strings representing relative file paths to exclude from "git rm".
    """
    log = logging.getLogger(__name__)
    remote_url = run_command(local_root, ['git', 'ls-remote', '--get-url', 'origin']).strip()
    if remote_url == 'origin':
        raise GitError('Git repo missing remote "origin".', remote_url)

    # Clone.
    try:
        run_command(new_root, ['git', 'clone', remote_url, '--depth=1', '--branch', branch, '.'])
    except CalledProcessError as exc:
        raise GitError('Failed to clone from remote repo URL.', exc.output)

    # Make sure user didn't select a tag as their DEST_BRANCH.
    try:
        run_command(new_root, ['git', 'symbolic-ref', 'HEAD'])
    except CalledProcessError as exc:
        raise GitError('Specified branch is not a real branch.', exc.output)

    # Done if no exclude.
    if not exclude:
        return

    # Resolve exclude paths.
    exclude_joined = [
        os.path.relpath(p, new_root) for e in exclude for p in glob.glob(os.path.join(new_root, rel_dest, e))
    ]
    log.debug('Expanded %s to %s', repr(exclude), repr(exclude_joined))

    # Do "git rm".
    try:
        run_command(new_root, ['git', 'rm', '-rf', rel_dest])
    except CalledProcessError as exc:
        raise GitError('"git rm" failed to remove ' + rel_dest, exc.output)

    # Restore files in exclude.
    run_command(new_root, ['git', 'reset', 'HEAD'] + exclude_joined)
    run_command(new_root, ['git', 'checkout', '--'] + exclude_joined)


def commit_and_push(local_root, versions):
    """Commit changed, new, and deleted files in the repo and attempt to push the branch to origin.

    :raise CalledProcessError: Unhandled git command failure.
    :raise GitError: Conflicting changes made in remote by other client and bad git config for commits.

    :param str local_root: Local path to git root directory.
    :param sphinxcontrib.versioning.versions.Versions versions: Versions class instance.

    :return: If push succeeded.
    :rtype: bool
    """
    log = logging.getLogger(__name__)
    current_branch = run_command(local_root, ['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
    run_command(local_root, ['git', 'add', '.'])

    # Check if there are no changes.
    try:
        run_command(local_root, ['git', 'diff', 'HEAD', '--no-ext-diff', '--quiet', '--exit-code'])
    except CalledProcessError:
        pass  # Repo is dirty, something has changed.
    else:
        log.info('No changes to commit.')
        return True

    # Check if there are changes excluding those files that always change.
    output = run_command(local_root, ['git', 'diff', 'HEAD', '--no-ext-diff', '--name-status'])
    for status, name in (l.split('\t', 1) for l in output.splitlines()):
        if status != 'M':
            break  # Only looking for modified files.
        components = name.split(os.sep)
        if '.doctrees' not in components and components[-1] != 'searchindex.js':
            break  # Something other than those two dirs/files has changed.
    else:
        log.info('No significant changes to commit.')
        return True

    # Commit.
    latest_commit = sorted(versions.remotes, key=lambda v: v['date'])[-1]
    commit_message_file = os.path.join(local_root, '_scv_commit_message.txt')
    with open(commit_message_file, 'w') as handle:
        handle.write('AUTO sphinxcontrib-versioning {} {}\n\n'.format(
            datetime.utcfromtimestamp(latest_commit['date']).strftime('%Y%m%d'),
            latest_commit['sha'][:11],
        ))
        for line in ('{}: {}\n'.format(v, os.environ[v]) for v in WHITELIST_ENV_VARS if v in os.environ):
            handle.write(line)
    try:
        run_command(local_root, ['git', 'commit', '-F', commit_message_file])
    except CalledProcessError as exc:
        raise GitError('Failed to commit locally.', exc.output)
    os.remove(commit_message_file)

    # Push.
    try:
        run_command(local_root, ['git', 'push', 'origin', current_branch])
    except CalledProcessError as exc:
        if '[rejected]' in exc.output and '(fetch first)' in exc.output:
            log.debug('Remote has changed since cloning the repo. Must retry.')
            return False
        raise GitError('Failed to push to remote.', exc.output)

    log.info('Successfully pushed to remote repository.')
    return True
