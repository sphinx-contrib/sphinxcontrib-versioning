"""Common objects imported by tests."""

from subprocess import check_output, STDOUT


def git_init(tmpdir):
    """Initialize local git repo.

    :param tmpdir: pytest fixture.
    """
    check_output(['git', 'init'], cwd=str(tmpdir), stderr=STDOUT)
