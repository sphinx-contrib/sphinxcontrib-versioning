"""Test function."""

import pytest

from sphinxcontrib.versioning.lib import HandledError
from sphinxcontrib.versioning.sphinx_ import read_config


@pytest.mark.parametrize('mode', ['default', 'overflow', 'conf.py'])
def test(local_docs, mode):
    """Verify working.

    :param local_docs: conftest fixture.
    :param str mode: Test scenario.
    """
    overflow = list()
    expected = 'contents'

    if mode == 'overflow':
        local_docs.join('contents.rst').rename(local_docs.join('index.rst'))
        overflow.extend(['-D', 'master_doc=index'])
        expected = 'index'
    elif mode == 'conf.py':
        local_docs.join('contents.rst').rename(local_docs.join('index2.rst'))
        local_docs.join('conf.py').write('master_doc = "index2"\n')
        expected = 'index2'

    config = read_config(str(local_docs), 'master', overflow)
    assert config['master_doc'] == expected


def test_sphinx_error(local_docs):
    """Test error handling.

    :param local_docs: conftest fixture.
    """
    local_docs.join('conf.py').write('undefined')
    with pytest.raises(HandledError):
        read_config(str(local_docs), 'master', list())
