"""Test objects in module."""

import pytest

from sphinxcontrib.versioning.lib import Config


def test_config():
    """Test Config."""
    config = Config()
    config.update(dict(invert=True, overflow=('-D', 'key=value'), root_ref='master', verbose=1))

    # Verify values.
    assert config.greatest_tag is False
    assert config.invert is True
    assert config.overflow == ('-D', 'key=value')
    assert config.root_ref == 'master'
    assert config.verbose == 1
    expected = ("<sphinxcontrib.versioning.lib.Config "
                "program_state={}, verbose=1, root_ref='master', overflow=('-D', 'key=value')>")
    assert repr(config) == expected

    # Test exceptions.
    with pytest.raises(AttributeError) as exc:
        config.update(dict(unknown=True))
    assert exc.value.args[0] == "'Config' object has no attribute 'unknown'"
    with pytest.raises(AttributeError) as exc:
        config.update(dict(invert=False))
    assert exc.value.args[0] == "'Config' object does not support item re-assignment on 'invert'"
