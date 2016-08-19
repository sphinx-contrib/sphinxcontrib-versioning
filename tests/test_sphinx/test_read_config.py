"""Test function."""

import pytest

from sphinxcontrib.versioning.lib import HandledError
from sphinxcontrib.versioning.sphinx_ import read_config


@pytest.mark.parametrize('mode', ['default', 'overflow', 'conf.py'])
def test(config, local_docs, mode):
    """Verify working.

    :param sphinxcontrib.versioning.lib.Config config: conftest fixture.
    :param local_docs: conftest fixture.
    :param str mode: Test scenario.
    """
    expected = 'contents'

    if mode == 'overflow':
        local_docs.join('contents.rst').rename(local_docs.join('index.rst'))
        config.overflow += ('-D', 'master_doc=index')
        expected = 'index'
    elif mode == 'conf.py':
        local_docs.join('contents.rst').rename(local_docs.join('index2.rst'))
        local_docs.join('conf.py').write('master_doc = "index2"\n')
        expected = 'index2'

    config = read_config(str(local_docs), 'master')
    assert config['master_doc'] == expected
    assert sorted(config['found_docs']) == [expected, 'one', 'three', 'two']


def test_sphinx_error(local_docs):
    """Test error handling.

    :param local_docs: conftest fixture.
    """
    local_docs.join('conf.py').write('undefined')
    with pytest.raises(HandledError):
        read_config(str(local_docs), 'master')
