"""Functions that perform main tasks. Code is here instead of in __main__.py."""

import json
import logging
import os
import re
import subprocess

from sphinxcontrib.versioning.git import export, fetch_commits, filter_and_date, get_root, GitError, list_remote
from sphinxcontrib.versioning.lib import HandledError, TempDir
from sphinxcontrib.versioning.sphinx_ import build, read_config

RE_INVALID_FILENAME = re.compile(r'[^0-9A-Za-z.-]')


def gather_git_info(cwd, conf_rel_paths):
    """Gather info about the remote git repository. Get list of refs.

    :raise HandledError: If function fails with a handled error. Will be logged before raising.

    :param str cwd: Current working directory to lookup git root.
    :param iter conf_rel_paths: List of possible relative paths (to git root) of Sphinx conf.py (e.g. docs/conf.py).

    :return: Local git root and commits with docs. Latter is a list of tuples: (sha, name, kind, date, conf_rel_path).
    :rtype: tuple
    """
    log = logging.getLogger(__name__)

    # Get root.
    log.debug('Current working directory: %s', cwd)
    try:
        root = get_root(cwd)
    except GitError as exc:
        log.error(exc.message)
        raise HandledError
    log.info('Working in git repository: %s', root)

    # List remote.
    log.info('Getting list of all remote branches/tags...')
    try:
        remotes = list_remote(root)
    except GitError as exc:
        log.error(exc.message)
        raise HandledError
    log.info('Found: %s', ' '.join(i[1] for i in remotes))

    # Filter and date.
    try:
        try:
            dates_paths = filter_and_date(root, conf_rel_paths, (i[0] for i in remotes))
        except GitError:
            log.info('Need to fetch from remote...')
            fetch_commits(root, remotes)
            try:
                dates_paths = filter_and_date(root, conf_rel_paths, (i[0] for i in remotes))
            except GitError as exc:
                log.error(exc.message)
                raise HandledError
    except subprocess.CalledProcessError as exc:
        log.debug(json.dumps(dict(command=exc.cmd, cwd=root, code=exc.returncode, output=exc.output)))
        log.error('Failed to get dates for all remote commits.')
        raise HandledError
    filtered_remotes = [[i[0], i[1], i[2], ] + dates_paths[i[0]] for i in remotes if i[0] in dates_paths]
    log.info('With docs: %s', ' '.join(i[1] for i in filtered_remotes))

    return root, filtered_remotes


def pre_build(local_root, versions, root_ref, overflow):
    """Build docs for all versions to determine URL (non-root directory name and master_doc names).

    Need to build docs to (a) avoid filename collision with files from root_ref and branch/tag names and (b) determine
    master_doc config values for all versions (in case master_doc changes from e.g. contents.rst to index.rst between
    versions).

    Exports all commits into a temporary directory and returns the path to avoid re-exporting during the final build.

    :param str local_root: Local path to git root directory.
    :param sphinxcontrib.versioning.versions.Versions versions: Version class instance.
    :param str root_ref: Branch/tag at the root of all HTML docs. Other branches/tags will be in subdirectories.
    :param list overflow: Overflow command line options to pass to sphinx-build.

    :return: Tempdir path with exported commits as subdirectories.
    :rtype: str
    """
    log = logging.getLogger(__name__)
    exported_root = TempDir().name
    root_remote = versions[root_ref]

    # Extract all.
    for sha in {r['sha'] for r in versions.remotes}:
        target = os.path.join(exported_root, sha)
        log.debug('Exporting %s to temporary directory.', sha)
        export(local_root, sha, target)

    # Build root ref.
    with TempDir() as temp_dir:
        log.debug('Building root ref (before setting URLs) in temporary directory: %s', temp_dir)
        source = os.path.dirname(os.path.join(exported_root, root_remote['sha'], root_remote['conf_rel_path']))
        build(source, temp_dir, versions, root_ref, overflow)
        existing = os.listdir(temp_dir)

    # Define directory paths in URLs in versions. Skip the root ref (will remain '.').
    for remote in (r for r in versions.remotes if r != root_remote):
        url = RE_INVALID_FILENAME.sub('_', remote['name'])
        while url in existing:
            url += '_'
        remote['url'] = url
        log.debug('%s has url %s', remote['name'], remote['url'])
        existing.append(url)

    # Define master_doc file paths in URLs in versions.
    for remote in list(versions.remotes):
        log.debug('Partially running sphinx-build to read configuration for: %s', remote['name'])
        source = os.path.dirname(os.path.join(exported_root, remote['sha'], remote['conf_rel_path']))
        try:
            config = read_config(source, remote['name'], overflow)
        except HandledError:
            log.warning('Skipping. Will not be building: %s', remote['name'])
            versions.remotes.pop(versions.remotes.index(remote))
            continue
        url = os.path.join(remote['url'], '{}.html'.format(config['master_doc']))
        if url.startswith('./'):
            url = url[2:]
        remote['url'] = url

    return exported_root
