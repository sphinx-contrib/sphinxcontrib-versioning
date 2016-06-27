#!/usr/bin/env python
"""Build versioned Sphinx docs for every branch and tag pushed to origin.

SOURCE is the path to the docs directory relative to the git root. Multiple
source directories may be specified in case your docs have moved around
between git tags.

DESTINATION is the directory path to the directory that will hold all
generated docs for all versions.

To pass additional options to sphinx-build (run for every branch/tag) use a
double hyphen (e.g. {program} build . /tmp/out -- -D setting=value).

Options may be set via environment variables using the SVB_ prefix (e.g.
SVB_RECENT_TAG=true or SVB_ROOT_REF=feature_branch).

Usage:
    {program} [options] build SOURCE... DESTINATION
    {program} -h | --help
    {program} -V | --version

Options:
    -h --help               Show this screen.
    -r REF --root-ref=REF   The branch/tag at the root of DESTINATION. All
                            others are in subdirectories [default: master].
    -t --greatest-tag       Override root-ref to be the tag with the highest
                            version number.
    -T --recent-tag         Override root-ref to be the most recent committed
                            tag.
    -v --verbose            Debug logging.
    -V --version            Print sphinxcontrib-versioning version.
"""

import logging
import sys

from docoptcfg import docoptcfg

from sphinxcontrib.versioning import __version__
from sphinxcontrib.versioning.lib import HandledError
from sphinxcontrib.versioning.setup_logging import setup_logging


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
    config = docoptcfg(docstring, argv=argv, config_option='--config', env_prefix='FAM_', version=__version__)
    config['overflow'] = overflow
    return config


def main(config):
    """Main function.

    :param dict config: Parsed command line arguments (get_arguments() output).
    """
    log = logging.getLogger(__name__)
    log.info('Running sphinxcontrib-versioning v%s', __version__)

    # Gather git data.
    log.info('Gathering info about the remote git repository...')
    assert config  # TODO


def entry_point():
    """Entry-point from setuptools."""
    try:
        config = get_arguments(sys.argv, __doc__)
        setup_logging(verbose=config['--verbose'])
        main(config)
    except HandledError:
        logging.critical('Failure.')
        sys.exit(1)
