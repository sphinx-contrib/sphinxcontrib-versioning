"""Interface with Sphinx."""

from jinja2.defaults import DEFAULT_NAMESPACE
from sphinx import build_main


def build(source, target, versions, overflow):
    """Build Sphinx docs for one version. Includes Versions class instance with names/urls in the HTML context.

    :param str source: Source directory to pass to sphinx-build.
    :param str target: Destination directory to write documentation to (passed to sphinx-build).
    :param sphinxcontrib.versioning.versions.Versions versions: Version class instance.
    :param list overflow: Overflow command line options to pass to sphinx-build.

    :return: Output of Sphinx build_main. 0 is success.
    :rtype: int
    """
    # Inject into Sphinx global objects.
    DEFAULT_NAMESPACE['versions'] = versions

    # Build.
    argv = ['sphinx-build', source, target] + overflow
    result = build_main(argv)
    return result
