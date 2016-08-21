.. _settings:

========
Settings
========

.. code-block:: bash

    sphinx-versioning [GLOBAL_OPTIONS] build [OPTIONS] REL_SOURCE... DESTINATION
    sphinx-versioning [GLOBAL_OPTIONS] push [OPTIONS] REL_SOURCE... DEST_BRANCH REL_DEST

SCVersioning reads settings from two sources:

* Your Sphinx **conf.py** file.
* Command line arguments.

Command line arguments always override anything set in conf.py. You can specify the path to conf.py with the
:option:`--local-conf` argument or SCVersioning will look at the first conf.py it finds in your :option:`REL_SOURCE`
directories. To completely disable using a conf.py file specify the :option:`--no-local-conf` command line argument.

Below are both the command line arguments available as well as the conf.py variable names SCVersioning looks for. All
conf.py variable names are prefixed with ``scv_``. An example:

.. code-block:: python

    # conf.py
    author = 'Your Name'
    project = 'My Project'
    scv_greatest_tag = True

Global Options
==============

These options apply to to both :ref:`build <build-arguments>` and :ref:`push <push-arguments>` sub commands. They must
be specified before the build/push command or else you'll get an error.

.. option:: -c <directory>, --chdir <directory>

    Change the current working directory of the program to this path.

.. option:: -g <directory>, --git-root <directory>

    Path to directory in the local repo. Default is the current working directory.

.. option:: -l <file>, --local-conf <file>

    Path to conf.py for SCVersioning to read its config from. Does not affect conf.py loaded by sphinx-build.

    If not specified the default behavior is to have SCVersioning look for a conf.py file in any :option:`REL_SOURCE`
    directory within the current working directory. Stops at the first conf.py found if any.

.. option:: -L, --no-local-conf

    Disables searching for or loading a local conf.py for SCVersioning settings. Does not affect conf.py loaded by
    sphinx-build.

.. option:: -N, --no-colors

    By default INFO, WARNING, and ERROR log/print statements use console colors. Use this argument to disable colors and
    log/print plain text.

.. option:: -v, --verbose

    Enable verbose/debug logging with timestamps and git command outputs. Implies :option:`--no-colors`. If specified
    more than once excess options (number used - 1) will be passed to sphinx-build.

.. _common-positional-arguments:

Common Positional Arguments
===========================

Both the :ref:`build <build-arguments>` and :ref:`push <push-arguments>` sub commands use these arguments.

.. option:: REL_SOURCE

    The path to the docs directory relative to the git root. If the source directory has moved around between git tags
    you can specify additional directories.

    This cannot be an absolute path, it must be relative to the root of your git repository. Sometimes projects move
    files around so documentation might not always have been in one place. To mitigate this you can specify additional
    relative paths and the first one that has a **conf.py** will be selected for each branch/tag. Any branch/tag that
    doesn't have a conf.py file in one of these REL_SOURCEs will be ignored.

.. option:: --, scv_overflow

    It is possible to give the underlying ``sphinx-build`` program command line options. SCVersioning passes everything
    after ``--`` to it. For example if you changed the theme for your docs between versions and want docs for all
    versions to have the same theme, you can run:

    .. code-block:: bash

        sphinx-versioning build docs docs/_build/html -- -A html_theme=sphinx_rtd_theme

    This setting may also be specified in your conf.py file. It must be a tuple of strings:

    .. code-block:: python

        scv_overflow = ("-A", "html_theme=sphinx_rtd_theme")

.. _build-arguments:

Build Arguments
===============

The ``build`` sub command builds all versions locally. It always gets the latest branches and tags from origin and
builds those doc files.

Positional Arguments
--------------------

In addition to the :ref:`common arguments <common-positional-arguments>`:

.. option:: DESTINATION

    The path to the directory that will hold all generated docs for all versions.

    This is the local path on the file sytem that will hold HTML files. It can be relative to the current working
    directory or an absolute directory path.

.. _build-options:

Options
-------

These options are available for the build sub command:

.. option:: -i, --invert, scv_invert

    Invert the order of branches/tags displayed in the sidebars in generated HTML documents. The default order is
    whatever git prints when running "**git ls-remote --heads --tags**".

    This setting may also be specified in your conf.py file. It must be a boolean:

    .. code-block:: python

        scv_invert = True

.. option:: -p <kind>, --priority <kind>, scv_priority

    ``kind`` may be either **branches** or **tags**. This argument is for themes that don't split up branches and tags
    in the generated HTML (e.g. sphinx_rtd_theme). This argument groups branches and tags together and whichever is
    selected for ``kind`` will be displayed first.

    This setting may also be specified in your conf.py file. It must be a string:

    .. code-block:: python

        scv_priority = 'branches'

.. option:: -r <ref>, --root-ref <ref>, scv_root_ref

    The branch/tag at the root of :option:`DESTINATION`. Will also be in subdirectories like the others. Default is
    **master**.

    If the root-ref does not exist or does not have docs, ``sphinx-versioning`` will fail and exit. The root-ref must
    have docs.

    This setting may also be specified in your conf.py file. It must be a string:

    .. code-block:: python

        scv_root_ref = 'feature_branch'

.. option:: -s <value>, --sort <value>, scv_sort

    Sort versions by one or more certain kinds of values. Valid values are ``semver``, ``alpha``, and ``time``.

    You can specify just one (e.g. "semver"), or more. The "semver" value sorts versions by
    `Semantic Versioning <http://semver.org/>`_, with the highest version being first (e.g. 3.0.0, 2.10.0, 1.0.0).
    Non-semver branches/tags will be sorted after all valid semver formats. This is where the multiple sort values come
    in. You can specify "alpha" to sort the remainder alphabetically or "time" to sort chronologically (most recent
    commit first).

    This setting may also be specified in your conf.py file. It must be a tuple of strings:

    .. code-block:: python

        scv_sort = ('semver',)

.. option:: -t, --greatest-tag, scv_greatest_tag

    Override root-ref to be the tag with the highest version number. If no tags have docs then this option is ignored
    and :option:`--root-ref` is used.

    This setting may also be specified in your conf.py file. It must be a boolean:

    .. code-block:: python

        scv_greatest_tag = True

.. option:: -T, --recent-tag, scv_recent_tag

    Override root-ref to be the most recent committed tag. If no tags have docs then this option is ignored and
    :option:`--root-ref` is used.

    This setting may also be specified in your conf.py file. It must be a boolean:

    .. code-block:: python

        scv_recent_tag = True

.. option:: -w <pattern>, --whitelist-branches <pattern>, scv_whitelist_branches

    Filter out branches not matching the pattern. Can be a simple string or a regex pattern. Specify multiple times to
    include more patterns in the whitelist.

    This setting may also be specified in your conf.py file. It must be a tuple of either strings or ``re.compile()``
    objects:

    .. code-block:: python

        scv_whitelist_branches = ('master', 'latest')

.. option:: -W <pattern>, --whitelist-tags <pattern>, scv_whitelist_tags

    Same as :option:`--whitelist-branches` but for git tags instead.

    This setting may also be specified in your conf.py file. It must be a tuple of either strings or ``re.compile()``
    objects:

    .. code-block:: python

        scv_whitelist_tags = (re.compile(r'^v\d+\.\d+\.\d+$'),)

.. _push-arguments:

Push Arguments
==============

``push`` does the same as build and also attempts to push generated HTML files to a remote branch. It will retry up to
three times in case of race conditions with other processes also trying to push files to the same branch (e.g. multiple
Jenkins/Travis jobs).

HTML files are committed to :option:`DEST_BRANCH` and pushed to origin.

Positional Arguments
--------------------

In addition to the :ref:`common arguments <common-positional-arguments>`:

.. option:: DEST_BRANCH

    The branch name where generated docs will be committed to. The branch will then be pushed to origin. If there is a
    race condition with another job pushing to origin the docs will be re-generated and pushed again.

    This must be a branch and not a tag. This also must already exist in origin.

.. option:: REL_DEST

    The path to the directory that will hold all generated docs for all versions relative to the git roof of
    DEST_BRANCH.

    If you want your generated **index.html** to be at the root of :option:`DEST_BRANCH` you can just specify a period
    (e.g. ``.``) for REL_DEST. If you want HTML files to be placed in say... "<git root>/html/docs", then you specify
    "html/docs".

Options
-------

All :ref:`build options <build-options>` are valid for the push sub command. Additionally these options are available
only for the push sub command:

.. option:: -e <file>, --grm-exclude <file>, scv_grm_exclude

    Causes "**git rm -rf $REL_DEST**" to run after checking out :option:`DEST_BRANCH` and then runs "git reset <file>"
    to preserve it. All other files in the branch in :option:`REL_DEST` will be deleted in the commit. You can specify
    multiple files or directories to be excluded by adding more ``--grm-exclude`` arguments.

    If this argument is not specified then nothing will be deleted from the branch. This may cause stale/orphaned HTML
    files in the branch if a branch is deleted from the repo after SCVersioning already created HTML files for it.

    This setting may also be specified in your conf.py file. It must be a tuple of strings:

    .. code-block:: python

        scv_grm_exclude = ('README.md', '.gitignore')
