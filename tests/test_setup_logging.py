"""Test objects in module."""

import logging
import logging.handlers
import sys
import time
from textwrap import dedent

import pytest

from sphinxcontrib.versioning.setup_logging import ColorFormatter, setup_logging


@pytest.mark.parametrize('verbose', [True, False])
def test_stdout_stderr(capsys, request, verbose):
    """Verify proper statements go to stdout or stderr.

    :param capsys: pytest fixture.
    :param request: pytest fixture.
    :param bool verbose: Verbose logging.
    """
    name = '{}_{}'.format(request.function.__name__, verbose)
    setup_logging(verbose=verbose, name=name)

    # Emit.
    logger = logging.getLogger(name)
    for attr in ('debug', 'info', 'warning', 'error', 'critical'):
        getattr(logger, attr)('Test {}.'.format(attr))
        time.sleep(0.01)

    # Collect.
    stdout, stderr = capsys.readouterr()

    # Check normal/verbose console.
    if verbose:
        assert name in stdout
        assert name in stderr
        assert 'Test debug.' in stdout
    else:
        assert name not in stdout
        assert name not in stderr
        assert 'Test debug.' not in stdout
    assert 'Test debug.' not in stderr

    assert 'Test info.' in stdout
    assert 'Test warning.' not in stdout
    assert 'Test error.' not in stdout
    assert 'Test critical.' not in stdout

    assert 'Test info.' not in stderr
    assert 'Test warning.' in stderr
    assert 'Test error.' in stderr
    assert 'Test critical.' in stderr


@pytest.mark.parametrize('verbose', [True, False])
def test_arrow(tmpdir, run, verbose):
    """Test => presence.

    :param tmpdir: pytest fixture.
    :param run: conftest fixture.
    :param bool verbose: Verbose logging.
    """
    assert ColorFormatter.SPECIAL_SCOPE == 'sphinxcontrib.versioning'

    logger_included = ColorFormatter.SPECIAL_SCOPE + '.sample'
    logger_excluded = 'test_sample'
    script = dedent("""\
    import logging
    from sphinxcontrib.versioning.setup_logging import setup_logging

    setup_logging(verbose={verbose})
    logging.getLogger("{included}").info("With arrow.")
    logging.getLogger("{excluded}").info("Without arrow.")
    """).format(verbose=verbose, included=logger_included, excluded=logger_excluded)
    tmpdir.join('script.py').write(script)

    output = run(tmpdir, [sys.executable, 'script.py'])
    if verbose:
        assert '=>' not in output
    else:
        assert '=> With arrow.' in output
        assert '\nWithout arrow.' in output


def test_colors(tmpdir, run):
    """Test colors.

    :param tmpdir: pytest fixture.
    :param run: conftest fixture.
    """
    script = dedent("""\
    import logging
    from sphinxcontrib.versioning.setup_logging import setup_logging

    setup_logging(verbose=False, colors=True)
    logger = logging.getLogger("{logger}")
    logger.critical("Critical")
    logger.error("Error")
    logger.warning("Warning")
    logger.info("Info")
    logger.debug("Debug")  # Not printed since verbose = False.
    """).format(logger=ColorFormatter.SPECIAL_SCOPE + '.sample')
    tmpdir.join('script.py').write(script)

    output = run(tmpdir, [sys.executable, 'script.py'])
    assert '\033[31m=> Critical\033[39m\n' in output
    assert '\033[31m=> Error\033[39m\n' in output
    assert '\033[33m=> Warning\033[39m\n' in output
    assert '\033[36m=> Info\033[39m' in output
    assert 'Debug' not in output
