"""Common objects used throughout the project."""

import atexit
import functools
import logging
import shutil
import tempfile
import weakref

import click


class Config(object):
    """The global configuration and state of the running program."""

    def __init__(self):
        """Constructor."""
        self.program_state = dict()

        # Booleans.
        self.greatest_tag = False
        self.invert = False
        self.no_colors = False
        self.recent_tag = False

        # Strings.
        self.chdir = None
        self.git_root = None
        self.priority = None
        self.root_ref = None

        # Tuples.
        self.grm_exclude = None
        self.overflow = None
        self.sort = None

        # Integers.
        self.verbose = 0

    def __repr__(self):
        """Class representation."""
        attributes = ('program_state', 'verbose', 'root_ref', 'overflow')
        key_value_attrs = ', '.join('{}={}'.format(a, repr(getattr(self, a))) for a in attributes)
        return '<{}.{} {}'.format(self.__class__.__module__, self.__class__.__name__, key_value_attrs)

    @classmethod
    def from_context(cls):
        """Retrieve this class' instance from the current Click context.

        :return: Instance of this class.
        :rtype: Config
        """
        try:
            ctx = click.get_current_context()
        except RuntimeError:
            return cls()
        return ctx.find_object(cls)

    def update(self, params):
        """Set instance values from dictionary.

        :param dict params: Click context params.
        """
        for key, value in params.items():
            if not hasattr(self, key):
                raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, key))
            setattr(self, key, value)


class HandledError(click.ClickException):
    """Abort the program."""

    def __init__(self):
        """Constructor."""
        super(HandledError, self).__init__(None)

    def show(self, **_):
        """Error messages should be logged before raising this exception."""
        logging.critical('Failure.')


class TempDir(object):
    """Similar to TemporaryDirectory in Python 3.x but with tuned weakref implementation."""

    def __init__(self, defer_atexit=False):
        """Constructor.

        :param bool defer_atexit: cleanup() to atexit instead of after garbage collection.
        """
        self.name = tempfile.mkdtemp('sphinxcontrib_versioning')
        if defer_atexit:
            atexit.register(shutil.rmtree, self.name, True)
            return
        try:
            weakref.finalize(self, shutil.rmtree, self.name, True)
        except AttributeError:
            weakref.proxy(self, functools.partial(shutil.rmtree, self.name, True))

    def __enter__(self):
        """Return directory path."""
        return self.name

    def __exit__(self, *_):
        """Cleanup when exiting context."""
        self.cleanup()

    def cleanup(self):
        """Recursively delete directory."""
        shutil.rmtree(self.name)
