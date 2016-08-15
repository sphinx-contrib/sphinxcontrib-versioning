"""Interface with Sphinx."""

from __future__ import print_function

import logging
import multiprocessing
import os
import sys

from sphinx import application, build_main
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.config import Config as SphinxConfig
from sphinx.errors import SphinxError
from sphinx.jinja2glue import SphinxFileSystemLoader

from sphinxcontrib.versioning import __version__
from sphinxcontrib.versioning.lib import Config, HandledError, TempDir
from sphinxcontrib.versioning.versions import Versions

SC_VERSIONING_VERSIONS = list()  # Updated after forking.


class EventHandlers(object):
    """Hold Sphinx event handlers as static or class methods.

    :ivar multiprocessing.queues.Queue ABORT_AFTER_READ: Communication channel to parent process.
    :ivar str CURRENT_VERSION: Current version being built.
    :ivar sphinxcontrib.versioning.versions.Versions VERSIONS: Versions class instance.
    """

    ABORT_AFTER_READ = None
    CURRENT_VERSION = None
    VERSIONS = None

    @staticmethod
    def builder_inited(app):
        """Update the Sphinx builder.

        :param sphinx.application.Sphinx app: Sphinx application object.
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
    def env_updated(cls, app, env):
        """Abort Sphinx after initializing config and discovering all pages to build.

        :param sphinx.application.Sphinx app: Sphinx application object.
        :param sphinx.environment.BuildEnvironment env: Sphinx build environment.
        """
        if cls.ABORT_AFTER_READ:
            config = {n: getattr(app.config, n) for n in (a for a in dir(app.config) if a.startswith('scv_'))}
            config['found_docs'] = tuple(str(d) for d in env.found_docs)
            config['master_doc'] = str(app.config.master_doc)
            cls.ABORT_AFTER_READ.put(config)
            sys.exit(0)

    @classmethod
    def html_page_context(cls, app, pagename, templatename, context, doctree):
        """Update the Jinja2 HTML context, exposes the Versions class instance to it.

        :param sphinx.application.Sphinx app: Sphinx application object.
        :param str pagename: Name of the page being rendered (without .html or any file extension).
        :param str templatename: Page name with .html.
        :param dict context: Jinja2 HTML context.
        :param docutils.nodes.document doctree: Tree of docutils nodes.
        """
        assert templatename or doctree  # Unused, for linting.
        versions = cls.VERSIONS.copy(pagename.count('/'), pagename)
        this_remote = versions[cls.CURRENT_VERSION]

        # Update Jinja2 context.
        context['bitbucket_version'] = cls.CURRENT_VERSION
        context['current_version'] = cls.CURRENT_VERSION
        context['github_version'] = cls.CURRENT_VERSION
        context['html_theme'] = app.config.html_theme
        context['scv_is_branch'] = this_remote['kind'] == 'heads'
        context['scv_is_greatest_tag'] = this_remote == versions.greatest_tag_remote
        context['scv_is_recent_branch'] = this_remote == versions.recent_branch_remote
        context['scv_is_recent_ref'] = this_remote == versions.recent_remote
        context['scv_is_recent_tag'] = this_remote == versions.recent_tag_remote
        context['scv_is_root_ref'] = this_remote == versions.root_remote
        context['scv_is_tag'] = this_remote['kind'] == 'tags'
        context['scv_root_ref_is_branch'] = versions.root_remote['kind'] == 'heads'
        context['scv_root_ref_is_tag'] = versions.root_remote['kind'] == 'tags'
        context['versions'] = versions


def setup(app):
    """Called by Sphinx during phase 0 (initialization).

    :param sphinx.application.Sphinx app: Sphinx application object.

    :returns: Extension version.
    :rtype: dict
    """
    # Used internally. For rebuilding all pages when one or more non-root-ref fails.
    app.add_config_value('sphinxcontrib_versioning_versions', SC_VERSIONING_VERSIONS, 'html')

    # Tell Sphinx which config values can be set by the user.
    for name, default in Config():
        app.add_config_value('scv_{}'.format(name), default, 'html')

    # Event handlers.
    app.connect('builder-inited', EventHandlers.builder_inited)
    app.connect('env-updated', EventHandlers.env_updated)
    app.connect('html-page-context', EventHandlers.html_page_context)
    return dict(version=__version__)


class ConfigInject(SphinxConfig):
    """Inject this extension info self.extensions. Append after user's extensions."""

    def __init__(self, dirname, filename, overrides, tags):
        """Constructor."""
        super(ConfigInject, self).__init__(dirname, filename, overrides, tags)
        self.extensions.append('sphinxcontrib.versioning.sphinx_')


def _build(argv, versions, current_name):
    """Build Sphinx docs via multiprocessing for isolation.

    :param tuple argv: Arguments to pass to Sphinx.
    :param sphinxcontrib.versioning.versions.Versions versions: Versions class instance.
    :param str current_name: The ref name of the current version being built.
    """
    # Patch.
    application.Config = ConfigInject
    EventHandlers.CURRENT_VERSION = current_name
    EventHandlers.VERSIONS = versions
    SC_VERSIONING_VERSIONS[:] = list(versions)

    # Update argv.
    config = Config.from_context()
    if config.verbose > 1:
        argv += ('-v',) * (config.verbose - 1)
    if config.no_colors:
        argv += ('-N',)

    # Build.
    result = build_main(argv)
    if result != 0:
        raise SphinxError


def _read_config(argv, current_name, queue):
    """Read the Sphinx config via multiprocessing for isolation.

    :param tuple argv: Arguments to pass to Sphinx.
    :param str current_name: The ref name of the current version being built.
    :param multiprocessing.queues.Queue queue: Communication channel to parent process.
    """
    # Patch.
    EventHandlers.ABORT_AFTER_READ = queue

    # Run.
    _build(argv, Versions(list()), current_name)


def build(source, target, versions, current_name, overflow):
    """Build Sphinx docs for one version. Includes Versions class instance with names/urls in the HTML context.

    :raise HandledError: If sphinx-build fails. Will be logged before raising.

    :param str source: Source directory to pass to sphinx-build.
    :param str target: Destination directory to write documentation to (passed to sphinx-build).
    :param sphinxcontrib.versioning.versions.Versions versions: Versions class instance.
    :param str current_name: The ref name of the current version being built.
    :param tuple overflow: Overflow command line options to pass to sphinx-build.
    """
    log = logging.getLogger(__name__)
    argv = ('sphinx-build', source, target) + overflow
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
    :param tuple overflow: Overflow command line options to pass to sphinx-build.

    :return: Specific Sphinx config values.
    :rtype: dict
    """
    log = logging.getLogger(__name__)
    queue = multiprocessing.Queue()

    with TempDir() as temp_dir:
        argv = ('sphinx-build', source, temp_dir) + overflow
        log.debug('Running sphinx-build for config values with args: %s', str(argv))
        child = multiprocessing.Process(target=_read_config, args=(argv, current_name, queue))
        child.start()
        child.join()  # Block.
        if child.exitcode != 0:
            log.error('sphinx-build failed for branch/tag while reading config: %s', current_name)
            raise HandledError

    config = queue.get()
    return config
