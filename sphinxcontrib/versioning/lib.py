"""Common objects used throughout the project."""

import shutil
import tempfile

try:
    from tempfile import TemporaryDirectory
    assert TemporaryDirectory
except ImportError:
    class TemporaryDirectory(object):
        """Create and return a temporary directory.

        This has the same behavior as mkdtemp but can be used as a context manager. Upon exiting the context, the
        directory and everything contained in it are removed.
        """

        def __init__(self):
            """Constructor."""
            self.name = tempfile.mkdtemp()

        def __enter__(self):
            """Return directory path."""
            return self.name

        def __exit__(self, *_):
            """Cleanup when exiting context."""
            self.cleanup()

        def cleanup(self):
            """Recursively delete directory."""
            shutil.rmtree(self.name)


class HandledError(Exception):
    """Generic exception used to signal raise HandledError() in scripts."""

    pass
