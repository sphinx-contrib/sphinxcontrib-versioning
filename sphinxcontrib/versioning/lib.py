"""Common objects used throughout the project."""

import atexit
import functools
import shutil
import tempfile
import weakref


class Config(object):
    """The global configuration for the project. Should be instantiated only at the beginning of run-time."""

    def __init__(self):
        """Constructor."""
        # Booleans.
        self.build = False
        self.greatest_tag = False
        self.invert = False
        self.no_colors = False
        self.recent_tag = False
        self.verbose = False

        # Strings.
        self.chdir = None
        self.destination = None
        self.dst_branch = None
        self.prioritize = None
        self.rel_dst = None
        self.rel_source = None
        self.root_ref = None

        # Tuples.
        self.grm_exclude = None
        self.overflow = None
        self.sort = None

    @classmethod
    def from_docopt(cls, config):
        """Docopt bridge. Reads dict from docopt, instantiates class, and copies values.

        :param dict config: Docopt config.

        :return: Class instance.
        :rtype: Config
        """
        self = cls()
        for key, value in config.items():
            if not key.startswith('--'):
                setattr(self, key.lower(), value)
                continue
            name = key[2:].replace('-', '_')
            setattr(self, name, value)
        return self


class HandledError(Exception):
    """Generic exception used to signal raise HandledError() in scripts."""

    pass


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
