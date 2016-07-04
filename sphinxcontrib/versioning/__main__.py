#!/usr/bin/env python
"""Build versioned Sphinx docs for every branch and tag pushed to origin.

SOURCE is the path to the docs directory relative to the git root. If the
source directory has moved around between git tags you can specify additional
directories with one or more --additional-src.

DESTINATION is the directory path to the directory that will hold all
generated docs for all versions.

To pass options to sphinx-build (run for every branch/tag) use a double hyphen
(e.g. {program} build /tmp/out docs -- -D setting=value).

Usage:
    {program} [options] [-s DIR...] build SOURCE DESTINATION
    {program} -h | --help
    {program} -V | --version

Options:
    -h --help               Show this screen.
    --invert                Invert/reverse order of versions.
    --prioritize=KIND       Set to "branches" or "tags" to group those kinds
                            of versions at the top (for themes that don't
                            separate them).
    -r REF --root-ref=REF   The branch/tag at the root of DESTINATION. All
                            others are in subdirectories [default: master].
    -s DIR --additional-src Additional/fallback relative source paths to look
                            for. Stops when conf.py is found.
    -S OPTS --sort=OPTS     Sort versions by one or more (comma separated):
                            semver, alpha, chrono
    -t --greatest-tag       Override root-ref to be the tag with the highest
                            version number.
    -T --recent-tag         Override root-ref to be the most recent committed
                            tag.
    -v --verbose            Debug logging.
    -V --version            Print sphinxcontrib-versioning version.
"""

import logging
import os
import sys

from docopt import docopt

from sphinxcontrib.versioning import __version__
from sphinxcontrib.versioning.lib import HandledError
from sphinxcontrib.versioning.routines import gather_git_info
from sphinxcontrib.versioning.setup_logging import setup_logging
from sphinxcontrib.versioning.versions import Versions


def get_arguments(argv, doc):
    """Get command line arguments.

    :param iter argv: Arguments to pass (e.g. sys.argv).
    :param str doc: Docstring to pass to docopt.

    :return: Parsed options with overflow options in the "overflow" key.
    :rtype: dict
    """
    if '--' in argv:
        pos = argv.index('--')
        argv, overflow = argv[:pos], argv[pos + 1:]
    else:
        argv, overflow = argv, list()
    docstring = doc.format(program='sphinx-versioning')
    config = docopt(docstring, argv=argv[1:], version=__version__)
    config['overflow'] = overflow
    return config


def main(config):
    """Main function.

    :param dict config: Parsed command line arguments (get_arguments() output).

    :return: Error code.
    :rtype: int
    """
    log = logging.getLogger(__name__)
    log.info('Running sphinxcontrib-versioning v%s', __version__)

    # Gather git data.
    log.info('Gathering info about the remote git repository...')
    conf_rel_paths = [os.path.join(s, 'conf.py') for s in [config['SOURCE']] + config['--additional-src']]
    filtered_remotes = gather_git_info(os.getcwd(), conf_rel_paths)[1]
    if not filtered_remotes:
        log.warning('No docs found in any remote branch/tag. Nothing to do.')
        return 1
    if config['--root-ref'] not in [r[1] for r in filtered_remotes]:
        log.warning('Root ref %s not found in: %s', config['--root-ref'], ' '.join(r[1] for r in filtered_remotes))
        return 1

    # Setup Jinja2 environment.
    versions = Versions(
        filtered_remotes,
        sort=(config['--sort'] or '').split(','),
        prioritize=config['--prioritize'],
        invert=config['--invert'],
    )
    assert versions
    return 0


def entry_point():
    """Entry-point from setuptools."""
    try:
        config = get_arguments(sys.argv, __doc__)
        setup_logging(verbose=config['--verbose'])
        sys.exit(main(config))
    except HandledError:
        logging.critical('Failure.')
        sys.exit(1)
