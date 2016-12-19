.. _tutorial:

========
Tutorial
========

This guide will go over the basics of the project.

Make sure that you've already :ref:`installed <install>` it.

Building Docs Locally
=====================

Before we begin make sure you have some Sphinx docs already in your project. If not read
`First Steps with Sphinx <http://www.sphinx-doc.org/en/stable/tutorial.html>`_ first. If you just want something quick
and dirty you can do the following:

.. code-block:: bash

    git checkout -b feature_branch master  # Create new branch from master.
    mkdir docs  # All documentation will go here (optional, can be anywhere).
    echo "master_doc = 'index'" > docs/conf.py  # Create Sphinx config file.
    echo -e "Test\n====\n\nSample Documentation" > docs/index.rst  # Create one doc.
    git add docs
    git commit
    git push origin feature_branch  # Required.

.. note::

    It is **required** to push doc files to origin. SCVersioning only works with remote branches/tags and ignores any
    local changes (committed, staged, unstaged, etc). If you don't push to origin SCVersioning won't see them. This
    eliminates race conditions when multiple CI jobs are building docs at the same time.

.. _build-all-versions:

Build All Versions
------------------

Now that you've got docs pushed to origin and they build fine with ``sphinx-build`` let's try building them with
SCVersioning:

.. code-block:: bash

    sphinx-versioning build -r feature_branch docs docs/_build/html
    open docs/_build/html/index.html

More information about all of the options can be found at :ref:`settings` or by running with ``--help`` but just for
convenience:

* ``-r feature_branch`` tells the program to build our newly created/pushed branch at the root of the "html" directory.
  We do this assuming there are no docs in master yet. Otherwise you can omit this argument.
* ``docs/_build/html`` is the destination directory that holds generated HTML files.
* The final ``docs`` argument is the directory where we put our RST files in, relative to the git root (e.g. if you
  clone your repo to another directory, that would be the git root directory). You can add more relative paths if you've
  moved the location of your RST files between different branches/tags.

The command should have worked and your docs should be available in **docs/_build/html/index.html** with a "Versions"
section in the sidebar.

If all you want SCVersioning to do is build docs for you for all versions and let you handle pushing them to a web host
and hosting them yourself then you are done here. Otherwise if you want to use the ``push`` feature then keep reading.

.. _pushing-to-remote-branch:

Pushing to Remote Branch
========================

SCVersioning supports pushing generated HTML files of your documentation to a remote branch, handling retries in case of
race conditions where other parallel jobs try to build docs and push them to the same branch.

Building on the previous section above let's go ahead and push those docs to a branch called ``gh-pages``. The branch
must already exist before trying to use the push feature, branches won't be automatically created. So let's do that:

.. code-block:: bash

    git checkout --orphan gh-pages  # Create the required branch with no history.
    git reset .gitignore  # Optionally keep your .gitignore.
    git rm -rf .  # Delete staged files left over from your previous branch.
    echo "My project's documentation." > README.rst  # Nice to have in all branches.
    git add README.rst .gitignore
    git commit  # Initial commit.
    git push origin gh-pages

Since this branch will just host HTML pages you can create an orphaned branch with no history instead of cluttering it
up with the history of your code changes.

.. _push-all-versions:

Push All Versions
-----------------

Now that you have the destination branch in origin go ahead and run SCVersioning:

.. code-block:: bash

    sphinx-versioning push -r feature_branch docs gh-pages .

Again you can find more information about all of the options at :ref:`settings` or by running with ``--help`` but just
for convenience:

* ``gh-pages`` is obviously the branch that will hold generated HTML docs.
* ``.`` is the path relative to the git root directory in the ``gh-pages`` branch where HTML files will be placed. If
  that branch will host other files like code coverage and you want users to navigate to
  http://domain.local/documentation/index.html instead of "/index.html" then replace "." with "documentation".
* The final ``docs`` argument is the directory where we put our RST files in just like the build command in the section
  above.

.. note::

    By default SCVersioning does not delete any files in the destination directory/branch. It only adds new
    ones or changes existing ones. This may lead to orphaned files in the branch if you delete branches/tags from the
    repository (their HTML files will be left behind in gh-pages and still accessible to your users). To enable the
    delete feature use one or more ``--grm-exclude <path>`` options. More info in :option:`--grm-exclude` or ``--help``.
