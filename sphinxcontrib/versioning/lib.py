"""Common objects used throughout the project."""

import shutil
import tempfile

try:
    from tempfile import TemporaryDirectory
except ImportError:
    TemporaryDirectory = None


class HandledError(Exception):
    """Generic exception used to signal raise HandledError() in scripts."""

    pass


class TemporaryDirectoryPy2(object):
    """TemporaryDirectory defined for Python 2.x since stdlib has it for only Python 3.x."""

    def __init__(self, suffix=''):
        """Constructor."""
        self.name = tempfile.mkdtemp(suffix)

    def __enter__(self):
        """Return directory path."""
        return self.name

    def __exit__(self, *_):
        """Cleanup when exiting context."""
        self.cleanup()

    def cleanup(self):
        """Recursively delete directory."""
        shutil.rmtree(self.name)


class TempDir(TemporaryDirectory or TemporaryDirectoryPy2):
    """Context manager for tempdir.mkdtemp()."""

    def __init__(self):
        """Constructor."""
        super(TempDir, self).__init__('sphinxcontrib_versioning')
