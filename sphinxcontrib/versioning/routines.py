"""Functions that perform main tasks. Code is here instead of in __main__.py."""

import json
import logging
import os
import re
import subprocess

from sphinxcontrib.versioning.git import export, fetch_commits, filter_and_date, GitError, list_remote
from sphinxcontrib.versioning.lib import HandledError, TempDir
from sphinxcontrib.versioning.sphinx_ import build, read_config

RE_INVALID_FILENAME = re.compile(r'[^0-9A-Za-z.-]')


def read_local_conf(local_conf, overflow):
    """Search for conf.py in any rel_source directory in CWD and if found read it and return.

    :param str local_conf: Path to conf.py to read.
    :param tuple overflow: Overflow command line options to pass to sphinx-build.

    :return: Loaded conf.py.
    :rtype: dict
    """
    log = logging.getLogger(__name__)

    # Attempt to read.
    log.info('Reading config from %s...', local_conf)
    try:
        config = read_config(os.path.dirname(local_conf), '<local>', overflow)
    except HandledError:
        log.warning('Unable to read file, continuing with only CLI args.')
        return dict()

    # Filter and return.
    return {k[4:]: v for k, v in config.items() if k.startswith('scv_') and not k[4:].startswith('_')}


def gather_git_info(root, conf_rel_paths, whitelist_branches, whitelist_tags):
    """Gather info about the remote git repository. Get list of refs.

    :raise HandledError: If function fails with a handled error. Will be logged before raising.

    :param str root: Root directory of repository.
    :param iter conf_rel_paths: List of possible relative paths (to git root) of Sphinx conf.py (e.g. docs/conf.py).
    :param iter whitelist_branches: Optional list of patterns to filter branches by.
    :param iter whitelist_tags: Optional list of patterns to filter tags by.

    :return: Commits with docs. A list of tuples: (sha, name, kind, date, conf_rel_path).
    :rtype: list
    """
    log = logging.getLogger(__name__)

    # List remote.
    log.info('Getting list of all remote branches/tags...')
    try:
        remotes = list_remote(root)
    except GitError as exc:
        log.error(exc.message)
        log.error(exc.output)
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
                log.error(exc.output)
                raise HandledError
    except subprocess.CalledProcessError as exc:
        log.debug(json.dumps(dict(command=exc.cmd, cwd=root, code=exc.returncode, output=exc.output)))
        log.error('Failed to get dates for all remote commits.')
        raise HandledError
    filtered_remotes = [[i[0], i[1], i[2], ] + dates_paths[i[0]] for i in remotes if i[0] in dates_paths]
    log.info('With docs: %s', ' '.join(i[1] for i in filtered_remotes))
    if not whitelist_branches and not whitelist_tags:
        return filtered_remotes

    # Apply whitelist.
    whitelisted_remotes = list()
    for remote in filtered_remotes:
        if remote[2] == 'heads' and whitelist_branches:
            if not any(re.search(p, remote[1]) for p in whitelist_branches):
                continue
        if remote[2] == 'tags' and whitelist_tags:
            if not any(re.search(p, remote[1]) for p in whitelist_tags):
                continue
        whitelisted_remotes.append(remote)
    log.info('Passed whitelisting: %s', ' '.join(i[1] for i in whitelisted_remotes))

    return whitelisted_remotes


def pre_build(local_root, versions, overflow):
    """Build docs for all versions to determine URL (non-root directory name and master_doc names).

    Need to build docs to (a) avoid filename collision with files from root_ref and branch/tag names and (b) determine
    master_doc config values for all versions (in case master_doc changes from e.g. contents.rst to index.rst between
    versions).

    Exports all commits into a temporary directory and returns the path to avoid re-exporting during the final build.

    :param str local_root: Local path to git root directory.
    :param sphinxcontrib.versioning.versions.Versions versions: Versions class instance.
    :param tuple overflow: Overflow command line options to pass to sphinx-build.

    :return: Tempdir path with exported commits as subdirectories.
    :rtype: str
    """
    log = logging.getLogger(__name__)
    exported_root = TempDir(True).name
    root_remote = versions.root_remote

    # Extract all.
    for sha in {r['sha'] for r in versions.remotes}:
        target = os.path.join(exported_root, sha)
        log.debug('Exporting %s to temporary directory.', sha)
        export(local_root, sha, target)

    # Build root ref.
    with TempDir() as temp_dir:
        log.debug('Building root ref (before setting URLs) in temporary directory: %s', temp_dir)
        source = os.path.dirname(os.path.join(exported_root, root_remote['sha'], root_remote['conf_rel_path']))
        build(source, temp_dir, versions, root_remote['name'], overflow)
        existing = os.listdir(temp_dir)

    # Define directory paths in URLs in versions. Skip the root ref (will remain '.').
    for remote in (r for r in versions.remotes if r != root_remote):
        url = RE_INVALID_FILENAME.sub('_', remote['name'])
        while url in existing:
            url += '_'
        remote['url'] = url
        log.debug('%s has url %s', remote['name'], remote['url'])
        existing.append(url)

    # Define master_doc file paths in URLs in versions and get found_docs for all versions.
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
        remote['found_docs'] = config['found_docs']

    return exported_root


def build_all(exported_root, destination, versions, overflow):
    """Build all versions.

    :param str exported_root: Tempdir path with exported commits as subdirectories.
    :param str destination: Destination directory to copy/overwrite built docs to. Does not delete old files.
    :param sphinxcontrib.versioning.versions.Versions versions: Versions class instance.
    :param tuple overflow: Overflow command line options to pass to sphinx-build.
    """
    log = logging.getLogger(__name__)
    root_remote = versions.root_remote

    while True:
        # Build root ref.
        log.info('Building root ref: %s', root_remote['name'])
        source = os.path.dirname(os.path.join(exported_root, root_remote['sha'], root_remote['conf_rel_path']))
        build(source, destination, versions, root_remote['name'], overflow)

        # Build other refs.
        for remote in list(r for r in versions.remotes if r != root_remote):
            log.info('Building ref: %s', remote['name'])
            source = os.path.dirname(os.path.join(exported_root, remote['sha'], remote['conf_rel_path']))
            target = os.path.join(destination, os.path.dirname(remote['url']))
            try:
                build(source, target, versions.copy(1), remote['name'], overflow)
            except HandledError:
                log.warning('Skipping. Will not be building %s. Rebuilding everything.', remote['name'])
                versions.remotes.pop(versions.remotes.index(remote))
                break  # Break out of for loop.
        else:
            break  # Break out of while loop if for loop didn't execute break statement above.
