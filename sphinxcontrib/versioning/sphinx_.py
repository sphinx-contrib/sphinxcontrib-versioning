"""Interface with Sphinx."""

import multiprocessing
import os
import sys

from sphinx import application, build_main
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.config import Config
from sphinx.jinja2glue import SphinxFileSystemLoader

from sphinxcontrib.versioning import __version__


class EventHandlers(object):
    """Hold Sphinx event handlers as static or class methods."""

    VERSIONS = None

    @staticmethod
    def builder_inited(app):
        """Update the Sphinx builder.

        :param app: Sphinx application object.
        """
        # Add this extension's _templates directory to Sphinx.
        templates_dir = os.path.join(os.path.dirname(__file__), '_templates')
        app.builder.templates.pathchain.append(templates_dir)
        app.builder.templates.loaders.append(SphinxFileSystemLoader(templates_dir))
        app.builder.templates.templatepathlen += 1

        # Add versions.html to sidebar.
        if '**' not in app.config.html_sidebars:
            app.config.html_sidebars['**'] = StandaloneHTMLBuilder.default_sidebars + ['versions.html']
        elif 'versions.html' not in app.config.html_sidebars['**']:
            app.config.html_sidebars['**'].append('versions.html')

    @classmethod
    def html_page_context(cls, *args):
        """Update the Jinja2 HTML context, exposes the Versions class instance to it.

        :param iter args: Arguments given by caller (Sphinx).
        """
        context = args[3]
        context['versions'] = cls.VERSIONS


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


def _build(argv, versions):
    """Build Sphinx docs via multiprocessing for isolation.

    :param iter argv: Arguments to pass to Sphinx.
    :param sphinxcontrib.versioning.versions.Versions versions: Version class instance.

    :return: Output of Sphinx build_main. 0 is success.
    :rtype: int
    """
    # Patch.
    application.Config = ConfigInject
    EventHandlers.VERSIONS = versions

    # Build.
    result = build_main(argv)
    sys.exit(result)


def build(source, target, versions, overflow):
    """Build Sphinx docs for one version. Includes Versions class instance with names/urls in the HTML context.

    :param str source: Source directory to pass to sphinx-build.
    :param str target: Destination directory to write documentation to (passed to sphinx-build).
    :param sphinxcontrib.versioning.versions.Versions versions: Version class instance.
    :param list overflow: Overflow command line options to pass to sphinx-build.

    :return: Output of Sphinx build_main. 0 is success.
    :rtype: int
    """
    argv = ['sphinx-build', source, target] + overflow
    child = multiprocessing.Process(target=_build, args=(argv, versions))
    child.start()
    child.join()  # Block.
    result = child.exitcode
    return result
