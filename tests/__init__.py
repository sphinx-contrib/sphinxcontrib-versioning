"""Common objects imported by tests."""

from subprocess import check_output, STDOUT


def git_init(tmpdir, bare=False):
    """Initialize local git repo.

    :param tmpdir: pytest fixture.
    :param bool bare: Initialize a bare (remote) repo.
    """
    if bare:
        command = ['git', 'init', '--bare']
    else:
        command = ['git', 'init']
    check_output(command, cwd=str(tmpdir), stderr=STDOUT)


def git_add_remote(tmpdir, name, url):
    """Add remotes to git repo.

    :param tmpdir: pytest fixture.
    :param str name: Remote name (e.g. origin).
    :param str url: Remote URL (e.g. file path to remote).
    """
    check_output(['git', 'remote', 'add', name, url], cwd=str(tmpdir), stderr=STDOUT)
