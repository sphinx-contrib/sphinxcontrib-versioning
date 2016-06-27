"""Code that handles logging for the project."""

import logging
import logging.handlers
import sys


def setup_logging(verbose=False, name=None):
    """Configure console logging. Info and below go to stdout, others go to stderr.

    :param bool verbose: Print debug statements.
    :param str name: Which logger name to set handlers to. Used for testing.
    """
    root_logger = logging.getLogger(name)
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if verbose:
        formatter = logging.Formatter('%(asctime)s %(process)-5d %(levelname)-8s %(name)-40s %(message)s')
    else:
        formatter = logging.Formatter('%(message)s')

    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setFormatter(formatter)
    handler_stdout.setLevel(logging.DEBUG)
    handler_stdout.addFilter(type('', (logging.Filter,), {'filter': staticmethod(lambda r: r.levelno <= logging.INFO)}))
    root_logger.addHandler(handler_stdout)

    handler_stderr = logging.StreamHandler(sys.stderr)
    handler_stderr.setFormatter(formatter)
    handler_stderr.setLevel(logging.WARNING)
    root_logger.addHandler(handler_stderr)
