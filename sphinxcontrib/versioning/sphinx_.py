"""Interface with Sphinx."""

from __future__ import print_function

import logging
import multiprocessing
import os

from sphinx import application, build_main, cmdline
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.config import Config
from sphinx.errors import SphinxError
from sphinx.jinja2glue import SphinxFileSystemLoader

from sphinxcontrib.versioning import __version__
from sphinxcontrib.versioning.lib import HandledError, TempDir


class EventHandlers(object):
    """Hold Sphinx event handlers as static or class methods.

    :ivar str CURRENT_VERSION: Current version being built.
    :ivar iter VERSIONS: List of version dicts.
    """

    CURRENT_VERSION = None
    VERSIONS = None

    @staticmethod
    def builder_inited(app):
        """Update the Sphinx builder.

        :param app: Sphinx application object.
        """
        # Add this extension's _templates directory to Sphinx.
        templates_dir = os.path.join(os.path.dirname(__file__), '_templates')
        app.builder.templates.pathchain.insert(0, templates_dir)
        app.builder.templates.loaders.insert(0, SphinxFileSystemLoader(templates_dir))
        app.builder.templates.templatepathlen += 1

        # Add versions.html to sidebar.
        if '**' not in app.config.html_sidebars:
            app.config.html_sidebars['**'] = StandaloneHTMLBuilder.default_sidebars + ['versions.html']
        elif 'versions.html' not in app.config.html_sidebars['**']:
            app.config.html_sidebars['**'].append('versions.html')

    @classmethod
    def html_page_context(cls, app, pagename, *args):
        """Update the Jinja2 HTML context, exposes the Versions class instance to it.

        :param app: Sphinx application object.
        :param str pagename: Relative path of RST file without the extension.
        :param iter args: Additional arguments given by Sphinx.
        """
        context = args[1]
        context['current_version'] = cls.CURRENT_VERSION
        context['html_theme'] = app.config.html_theme
        context['versions'] = cls.VERSIONS.copy(pagename.count('/'))


def setup(app):
    """Called by Sphinx during phase 0 (initialization).

    :param app: Sphinx application object.

    :returns: Extension version.
    :rtype: dict
    """
    app.connect('builder-inited', EventHandlers.builder_inited)
    app.connect('html-page-context', EventHandlers.html_page_context)
    return dict(version=__version__)


class SphinxBuildAbort(application.Sphinx):
    """Abort after initializing config and before build."""

    SPECIFIC_CONFIG = None

    def build(self, *_):
        """Instead of building read the config and store it in the class variable."""
        config = dict(
            master_doc=str(self.config.master_doc),
        )
        SphinxBuildAbort.SPECIFIC_CONFIG = config


class ConfigInject(Config):
    """Inject this extension info self.extensions. Append after user's extensions."""

    def __init__(self, dirname, filename, overrides, tags):
        """Constructor."""
        super(ConfigInject, self).__init__(dirname, filename, overrides, tags)
        self.extensions.append('sphinxcontrib.versioning.sphinx_')


def _build(argv, versions, current_name):
    """Build Sphinx docs via multiprocessing for isolation.

    :param iter argv: Arguments to pass to Sphinx.
    :param versions: Version class instance.
    :param str current_name: The ref name of the current version being built.
    """
    # Patch.
    application.Config = ConfigInject
    EventHandlers.CURRENT_VERSION = current_name
    EventHandlers.VERSIONS = versions

    # Build.
    result = build_main(argv)
    if result != 0:
        raise SphinxError


def _read_config(argv, current_name, queue):
    """Read the Sphinx config via multiprocessing for isolation.

    :param iter argv: Arguments to pass to Sphinx.
    :param str current_name: The ref name of the current version being built.
    :param multiprocessing.Queue queue: Communication channel to parent process.
    """
    # Patch.
    cmdline.Sphinx = SphinxBuildAbort

    # Run.
    _build(argv, None, current_name)

    # Store.
    queue.put(SphinxBuildAbort.SPECIFIC_CONFIG)


def build(source, target, versions, current_name, overflow):
    """Build Sphinx docs for one version. Includes Versions class instance with names/urls in the HTML context.

    :raise HandledError: If sphinx-build fails. Will be logged before raising.

    :param str source: Source directory to pass to sphinx-build.
    :param str target: Destination directory to write documentation to (passed to sphinx-build).
    :param sphinxcontrib.versioning.versions.Versions versions: Version class instance.
    :param str current_name: The ref name of the current version being built.
    :param list overflow: Overflow command line options to pass to sphinx-build.
    """
    log = logging.getLogger(__name__)
    argv = ['sphinx-build', source, target] + overflow
    log.debug('Running sphinx-build for %s with args: %s', current_name, str(argv))
    child = multiprocessing.Process(target=_build, args=(argv, versions, current_name))
    child.start()
    child.join()  # Block.
    if child.exitcode != 0:
        log.error('sphinx-build failed for branch/tag: %s', current_name)
        raise HandledError


def read_config(source, current_name, overflow):
    """Read the Sphinx config for one version.

    :raise HandledError: If sphinx-build fails. Will be logged before raising.

    :param str source: Source directory to pass to sphinx-build.
    :param str current_name: The ref name of the current version being built.
    :param list overflow: Overflow command line options to pass to sphinx-build.

    :return: Specific Sphinx config values.
    :rtype: dict
    """
    log = logging.getLogger(__name__)
    queue = multiprocessing.Queue()

    with TempDir() as temp_dir:
        argv = ['sphinx-build', source, temp_dir] + overflow
        log.debug('Running sphinx-build for config values with args: %s', str(argv))
        child = multiprocessing.Process(target=_read_config, args=(argv, current_name, queue))
        child.start()
        child.join()  # Block.
        if child.exitcode != 0:
            log.error('sphinx-build failed for branch/tag while reading config: %s', current_name)
            raise HandledError

    config = queue.get()
    return config
