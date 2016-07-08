"""Interface with Sphinx."""

import logging
import multiprocessing
import os
import sys

from sphinx import application, build_main
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.config import Config
from sphinx.jinja2glue import SphinxFileSystemLoader

from sphinxcontrib.versioning import __version__


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


class ConfigInject(Config):
    """Inject this extension info self.extensions. Append after user's extensions."""

    def __init__(self, dirname, filename, overrides, tags):
        """Constructor."""
        super(ConfigInject, self).__init__(dirname, filename, overrides, tags)
        self.extensions.append('sphinxcontrib.versioning.sphinx_')


def _build(argv, versions, current_name):
    """Build Sphinx docs via multiprocessing for isolation.

    :param iter argv: Arguments to pass to Sphinx.
    :param sphinxcontrib.versioning.versions.Versions versions: Version class instance.
    :param str current_name: The ref name of the current version being built.

    :return: Output of Sphinx build_main. 0 is success.
    :rtype: int
    """
    # Patch.
    application.Config = ConfigInject
    EventHandlers.CURRENT_VERSION = current_name
    EventHandlers.VERSIONS = versions

    # Build.
    result = build_main(argv)
    sys.exit(result)


def build(source, target, versions, current_name, overflow):
    """Build Sphinx docs for one version. Includes Versions class instance with names/urls in the HTML context.

    :param str source: Source directory to pass to sphinx-build.
    :param str target: Destination directory to write documentation to (passed to sphinx-build).
    :param sphinxcontrib.versioning.versions.Versions versions: Version class instance.
    :param str current_name: The ref name of the current version being built.
    :param list overflow: Overflow command line options to pass to sphinx-build.

    :return: Output of Sphinx build_main. 0 is success.
    :rtype: int
    """
    log = logging.getLogger(__name__)
    argv = ['sphinx-build', source, target] + overflow
    log.debug('Running sphinx-build for %s with args: %s', current_name, str(argv))
    child = multiprocessing.Process(target=_build, args=(argv, versions, current_name))
    child.start()
    child.join()  # Block.
    return child.exitcode
