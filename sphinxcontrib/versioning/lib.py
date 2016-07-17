"""Common objects used throughout the project."""

import atexit
import functools
import shutil
import tempfile
import weakref


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
        elif hasattr(weakref, 'finalize'):
            weakref.finalize(self, shutil.rmtree, self.name, True)
        else:
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
