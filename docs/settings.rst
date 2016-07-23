.. _settings:

========
Settings
========

SCVersioning reads settings only from command line arguments. Here are all the options will be listed along with their
descriptions.

.. code-block:: bash

    sphinx-versioning [options] build DESTINATION REL_SOURCE...
    sphinx-versioning [options] [-e F...] push DST_BRANCH REL_DST REL_SOURCE...

Global Arguments
================

These arguments/options apply to both :ref:`build <build-arguments>` and :ref:`push <push-arguments>` sub-commands.

.. option:: REL_SOURCE

    The path to the docs directory relative to the git root. If the source directory has moved around between git tags
    you can specify additional directories.

    This cannot be an absolute path, it must be relative to the root of your git repository. Sometimes projects move
    files around so documentation might not always have been in one place. To mitigate this you can specify additional
    relative paths and the first one that has a **conf.py** will be selected for each branch/tag. Any branch/tag that
    doesn't have a conf.py file in one of these REL_SOURCEs will be ignored.

.. option:: -c <directory>, --chdir <directory>

    Change the current working directory of the program to this path.

.. option:: -C, --no-colors

    By default INFO, WARNING, and ERROR log/print statements use console colors. Use this argument to disable colors and
    log/print plain text.

.. option:: -i, --invert

    Invert the order of branches/tags displayed in the sidebars in generated HTML documents. The default order is
    whatever git prints when running "**git ls-remote --heads --tags**".

.. option:: -p <kind>, --prioritize <kind>

    ``kind`` may be either **branches** or **tags**. This argument is for themes that don't split up branches and tags
    in the generated HTML (e.g. sphinx_rtd_theme). This argument groups branches and tags together and whichever is
    selected for ``kind`` will be displayed first.

.. option:: -r <ref>, --root-ref <ref>

    The branch/tag at the root of :option:`DESTINATION`. All others are in subdirectories. Default is **master**.

    If the root-ref does not exist or does not have docs, ``sphinx-versioning`` will fail and exit. The root-ref must
    have docs.

.. option:: -s <csv>, --sort <csv>

    Comma separated values to sort versions by. Valid values are ``semver``, ``alpha``, and ``chrono``.

    You can specify just one (e.g. "semver"), or more (e.g. "semver,alpha"). The "semver" value sorts versions by
    `Semantic Versioning <http://semver.org/>`_, with the highest version being first (e.g. 3.0.0, 2.10.0, 1.0.0).
    Non-semver branches/tags will be sorted after all valid semver formats. This is where the multiple sort values come
    in. You can specify "alpha" to sort the remainder alphabetically or "chrono" to sort chronologically (most recent
    commit first).

.. option:: -t, --greatest-tag

    Override root-ref to be the tag with the highest version number. If no tags have docs then this option is ignored
    and :option:`--root-ref` is used.

.. option:: -T, --recent-tag

    Override root-ref to be the most recent committed tag. If no tags have docs then this option is ignored and
    :option:`--root-ref` is used.

.. option:: -v, --verbose

    Enable verbose/debug logging with timestamps and git command outputs. Implies :option:`--no-colors`.

Overflow/Pass Options
---------------------

It is possible to give the underlying ``sphinx-build`` program comand line options. SCVersioning passes everything after
``--`` to it. For example if you changed the theme for your docs between versions and want docs for all versions to have
the same theme, you can run:

.. code-block:: bash

    sphinx-versioning build docs/_build/html docs -- -A html_theme=sphinx_rtd_theme

.. _build-arguments:

Build Arguments
===============

The ``build`` sub-command builds all versions locally. It always gets the latest branches and tags from origin and
builds those doc files. The above global arguments work for ``build`` in addition to:

.. option:: DESTINATION

    The path to the directory that will hold all generated docs for all versions.

    This is the local path on the file sytem that will hold HTML files. It can be relative to the current working
    directory or an absolute directory path.

.. _push-arguments:

Push Arguments
==============

``push`` does the same as push and also attempts to push generated HTML files to a remote branch. It will retry up to
three times in case of race conditions with other processes also trying to push files to the same branch (e.g. multiple
Jenkins/Travis jobs).

HTML files are committed to :option:`DST_BRANCH` and pushed to origin.

.. option:: DST_BRANCH

    The branch name where generated docs will be committed to. The branch will then be pushed to origin. If there is a
    race condition with another job pushing to origin the docs will be re-generated and pushed again.

    This must be a branch and not a tag. This also must already exist in origin.

.. option:: REL_DST

    The path to the directory that will hold all generated docs for all versions relative to the git roof of DST_BRANCH.

    If you want your generated **index.html** to be at the root of :option:`DST_BRANCH` you can just specify a period
    (e.g. ``.``) for REL_DST. If you want HTML files to be placed in say... "<git root>/html/docs", then you specify
    "html/docs".

.. option:: -e <file>, --grm-exclude <file>

    Causes "**git rm -rf $REL_DST**" to run after checking out :option:`DST_BRANCH` and then runs "git reset <file>" to
    preserve it. All other files in the branch in :option:`REL_DST` will be deleted in the commit. You can specify
    multiple files or directories to be excluded by adding more ``--grm-exclude`` arguments.

    If this argument is not specified then nothing will be deleted from the branch. This may cause stale/orphaned HTML
    files in the branch if a branch is deleted from the repo after SCVersioning already created HTML files for it.
