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
        self._already_set = set()
        self._program_state = dict()

        # Booleans.
        self.greatest_tag = False
        self.invert = False
        self.no_colors = False
        self.no_local_conf = False
        self.recent_tag = False

        # Strings.
        self.chdir = None
        self.git_root = None
        self.local_conf = None
        self.priority = None
        self.root_ref = 'master'

        # Tuples.
        self.grm_exclude = tuple()
        self.overflow = tuple()
        self.sort = tuple()
        self.whitelist_branches = tuple()
        self.whitelist_tags = tuple()

        # Integers.
        self.verbose = 0

    def __contains__(self, item):
        """Implement 'key in Config'.

        :param str item: Key to search for.

        :return: If item in self._program_state.
        :rtype: bool
        """
        return item in self._program_state

    def __iter__(self):
        """Yield names and current values of attributes that can be set from Sphinx config files."""
        for name in (n for n in dir(self) if not n.startswith('_') and not callable(getattr(self, n))):
            yield name, getattr(self, name)

    def __repr__(self):
        """Class representation."""
        attributes = ('_program_state', 'verbose', 'root_ref', 'overflow')
        key_value_attrs = ', '.join('{}={}'.format(a, repr(getattr(self, a))) for a in attributes)
        return '<{}.{} {}>'.format(self.__class__.__module__, self.__class__.__name__, key_value_attrs)

    def __setitem__(self, key, value):
        """Implement Config[key] = value, updates self._program_state.

        :param str key: Key to set in self._program_state.
        :param value: Value to set in self._program_state.
        """
        self._program_state[key] = value

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

    def pop(self, *args):
        """Pop item from self._program_state.

        :param iter args: Passed to self._program_state.

        :return: Object from self._program_state.pop().
        """
        return self._program_state.pop(*args)

    def update(self, params, ignore_set=False, overwrite=False):
        """Set instance values from dictionary.

        :param dict params: Click context params.
        :param bool ignore_set: Skip already-set values instead of raising AttributeError.
        :param bool overwrite: Allow overwriting already-set values.
        """
        log = logging.getLogger(__name__)
        valid = {i[0] for i in self}
        for key, value in params.items():
            if not hasattr(self, key):
                raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, key))
            if key not in valid:
                message = "'{}' object does not support item assignment on '{}'"
                raise AttributeError(message.format(self.__class__.__name__, key))
            if key in self._already_set:
                if ignore_set:
                    log.debug('%s already set in config, skipping.', key)
                    continue
                if not overwrite:
                    message = "'{}' object does not support item re-assignment on '{}'"
                    raise AttributeError(message.format(self.__class__.__name__, key))
            setattr(self, key, value)
            self._already_set.add(key)


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
