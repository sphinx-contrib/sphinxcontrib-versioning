"""Interface with git locally and remotely."""

from subprocess import CalledProcessError, check_output, STDOUT


class GitError(Exception):
    """Raised if git exits non-zero."""

    def __init__(self, message, output):
        """Constructor."""
        self.message = message
        super(GitError, self).__init__(message, output)


def get_root(directory):
    """Get root directory of the local git repo from any subdirectory within it.

    :raise GitError: If git command fails (dir not a git repo?).

    :param str directory: Subdirectory in the local repo.

    :return: Root directory of repository.
    :rtype: str
    """
    command = ['git', 'rev-parse', '--show-toplevel']
    try:
        output = check_output(command, cwd=directory, stderr=STDOUT).decode('ascii')
    except CalledProcessError as exc:
        raise GitError('Git failed to list remote refs.', exc.output)
    return output.strip()
