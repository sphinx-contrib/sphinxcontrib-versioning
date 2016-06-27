"""Test flash_air_music.setup_logging functions/classes."""

import logging
import logging.handlers
import time

import pytest

from sphinxcontrib.versioning.setup_logging import setup_logging


@pytest.mark.parametrize('verbose', [True, False])
def test_setup_logging_new(capsys, request, verbose):
    """Test setup_logging() function with no previous config.

    :param capsys: pytest fixture.
    :param request: pytest fixture.
    :param bool verbose: Verbose logging.
    """
    name = '{}_{}'.format(request.function.__name__, verbose)
    setup_logging(verbose, name)

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
