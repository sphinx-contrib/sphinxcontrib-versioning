"""Test function in module."""

import pytest

from sphinxcontrib.versioning.routines import read_local_conf


@pytest.mark.parametrize('error', [False, True])
def test_empty(tmpdir, caplog, error):
    """With no settings defined.

    :param tmpdir: pytest fixture.
    :param caplog: pytest extension fixture.
    :param bool error: Malformed conf.py.
    """
    tmpdir.ensure('contents.rst')
    local_conf = tmpdir.join('conf.py')
    if error:
        local_conf.write('undefined')
    else:
        local_conf.write('project = "MyProject"')

    # Run.
    config = read_local_conf(str(local_conf))
    records = [(r.levelname, r.message) for r in caplog.records]

    # Verify.
    if error:
        assert records[-1] == ('WARNING', 'Unable to read file, continuing with only CLI args.')
    else:
        assert [r[0] for r in records] == ['INFO', 'DEBUG']
    assert config == dict()


def test_settings(tmpdir):
    """Test with settings in conf.py.

    :param tmpdir: pytest fixture.
    """
    tmpdir.ensure('index.rst')
    local_conf = tmpdir.join('conf.py')
    local_conf.write(
        'import re\n\n'
        'master_doc = "index"\n'
        'project = "MyProject"\n'
        'scv__already_set = {"one", "two"}\n'
        'scv_already_set = {"three", "four"}\n'
        'scv_root_ref = "feature"\n'
        'scv_unknown_item = True\n'
    )

    # Run.
    config = read_local_conf(str(local_conf))

    # Verify.
    assert config == dict(root_ref='feature')
