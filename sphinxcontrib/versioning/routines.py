"""Functions that perform main tasks. Code is here instead of in __main__.py."""

import json
import logging
import subprocess

from sphinxcontrib.versioning.git import fetch_commits, filter_and_date, get_root, GitError, list_remote
from sphinxcontrib.versioning.lib import HandledError


def gather_git_info(cwd, conf_rel_paths):
    """Gather info about the remote git repository. Get list of refs.

    :param str cwd: Current working directory to lookup git root.
    :param iter conf_rel_paths: List of possible relative paths (to git root) of Sphinx conf.py (e.g. docs/conf.py).

    :return: Local git root and commits with docs. Latter is a list of tuples: (sha, name, kind, date).
    :rtype: tuple
    """
    log = logging.getLogger(__name__)

    # Get root.
    log.debug('Current working directory: %s', cwd)
    try:
        root = get_root(cwd)
    except GitError as exc:
        log.fatal(exc.message)
        raise HandledError
    log.info('Working in git repository: %s', root)

    # List remote.
    log.info('Getting list of all remote branches/tags...')
    try:
        remotes = list_remote(root)
    except GitError as exc:
        log.fatal(exc.message)
        raise HandledError
    log.info('Found: %s', ' '.join(i[1] for i in remotes))

    # Filter and date.
    try:
        try:
            dates = filter_and_date(root, conf_rel_paths, (i[0] for i in remotes))
        except GitError:
            log.info('Need to fetch from remote...')
            fetch_commits(root, remotes)
            try:
                dates = filter_and_date(root, conf_rel_paths, (i[0] for i in remotes))
            except GitError as exc:
                log.fatal(exc.message)
                raise HandledError
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode('utf-8')
        log.debug(json.dumps(dict(command=exc.cmd, cwd=root, code=exc.returncode, output=output)))
        log.fatal('Failed to get dates for all remote commits.')
        raise HandledError
    filtered_remotes = [(i[0], i[1], i[2], dates[i[0]]) for i in remotes if i[0] in dates]
    log.info('With docs: %s', ' '.join(i[1] for i in filtered_remotes))

    return root, filtered_remotes
