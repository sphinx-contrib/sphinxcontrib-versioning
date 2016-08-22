"""Test objects in module."""

import pytest

from sphinxcontrib.versioning.lib import Config


def test_config():
    """Test Config."""
    config = Config()
    config.update(dict(invert=True, overflow=('-D', 'key=value'), root_ref='master', verbose=1))

    # Verify values.
    assert config.banner_main_ref == 'master'
    assert config.greatest_tag is False
    assert config.invert is True
    assert config.overflow == ('-D', 'key=value')
    assert config.root_ref == 'master'
    assert config.verbose == 1
    assert repr(config) == ("<sphinxcontrib.versioning.lib.Config "
                            "_program_state={}, verbose=1, root_ref='master', overflow=('-D', 'key=value')>")

    # Verify iter.
    actual = sorted(config)
    expected = [
        ('banner_greatest_tag', False),
        ('banner_main_ref', 'master'),
        ('banner_recent_tag', False),
        ('chdir', None),
        ('git_root', None),
        ('greatest_tag', False),
        ('grm_exclude', tuple()),
        ('invert', True),
        ('local_conf', None),
        ('no_colors', False),
        ('no_local_conf', False),
        ('overflow', ('-D', 'key=value')),
        ('priority', None),
        ('recent_tag', False),
        ('root_ref', 'master'),
        ('show_banner', False),
        ('sort', tuple()),
        ('verbose', 1),
        ('whitelist_branches', tuple()),
        ('whitelist_tags', tuple()),
    ]
    assert actual == expected

    # Verify contains, setitem, and pop.
    assert getattr(config, '_program_state') == dict()
    assert 'key' not in config
    config['key'] = 'value'
    assert getattr(config, '_program_state') == dict(key='value')
    assert 'key' in config
    assert config.pop('key') == 'value'
    assert getattr(config, '_program_state') == dict()
    assert 'key' not in config
    assert config.pop('key', 'nope') == 'nope'
    assert getattr(config, '_program_state') == dict()
    assert 'key' not in config

    # Test exceptions.
    with pytest.raises(AttributeError) as exc:
        config.update(dict(unknown=True))
    assert exc.value.args[0] == "'Config' object has no attribute 'unknown'"
    with pytest.raises(AttributeError) as exc:
        config.update(dict(_program_state=dict(key=True)))
    assert exc.value.args[0] == "'Config' object does not support item assignment on '_program_state'"
    with pytest.raises(AttributeError) as exc:
        config.update(dict(invert=False))
    assert exc.value.args[0] == "'Config' object does not support item re-assignment on 'invert'"
