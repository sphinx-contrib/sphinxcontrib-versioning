"""Code that handles logging for the project."""

import logging
import logging.handlers
import sys

import colorclass


class ColorFormatter(logging.Formatter):
    """Custom logging formatter that introduces console colors if not verbose."""

    SPECIAL_SCOPE = __package__

    def __init__(self, verbose, colors):
        """Constructor.

        :param bool verbose: Enable verbose logging.
        :param bool colors: Enable colored output for statements emitted from this project.
        """
        self.verbose = verbose
        self.colors = colors
        if verbose:
            fmt = '%(asctime)s %(process)-5d %(levelname)-8s %(name)-40s %(message)s'
        else:
            fmt = '%(message)s'
        super(ColorFormatter, self).__init__(fmt)

    def format(self, record):
        """Apply little arrow and colors to the record.

        Arrow and colors are only applied to sphinxcontrib.versioning log statements.

        :param logging.LogRecord record: The log record object to log.
        """
        formatted = super(ColorFormatter, self).format(record)
        if self.verbose or not record.name.startswith(self.SPECIAL_SCOPE):
            return formatted

        # Arrow.
        formatted = '=> ' + formatted

        # Colors.
        if not self.colors:
            return formatted
        if record.levelno >= logging.ERROR:
            formatted = str(colorclass.Color.red(formatted))
        elif record.levelno >= logging.WARNING:
            formatted = str(colorclass.Color.yellow(formatted))
        else:
            formatted = str(colorclass.Color.cyan(formatted))
        return formatted


def setup_logging(verbose=0, colors=False, name=None):
    """Configure console logging. Info and below go to stdout, others go to stderr.

    :param int verbose: Verbosity level. > 0 print debug statements. > 1 passed to sphinx-build.
    :param bool colors: Print color text in non-verbose mode.
    :param str name: Which logger name to set handlers to. Used for testing.
    """
    root_logger = logging.getLogger(name)
    root_logger.setLevel(logging.DEBUG if verbose > 0 else logging.INFO)
    formatter = ColorFormatter(verbose > 0, colors)
    if colors:
        colorclass.Windows.enable()

    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setFormatter(formatter)
    handler_stdout.setLevel(logging.DEBUG)
    handler_stdout.addFilter(type('', (logging.Filter,), {'filter': staticmethod(lambda r: r.levelno <= logging.INFO)}))
    root_logger.addHandler(handler_stdout)

    handler_stderr = logging.StreamHandler(sys.stderr)
    handler_stderr.setFormatter(formatter)
    handler_stderr.setLevel(logging.WARNING)
    root_logger.addHandler(handler_stderr)
