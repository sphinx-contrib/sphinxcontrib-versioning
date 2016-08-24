.. _github_pages:

============
GitHub Pages
============

It's pretty easy to use `GitHub Pages <https://pages.github.com/>`_ to host all of your versioned documentation. Before
starting be sure to go through the :ref:`tutorial` first to make sure you can build your docs locally. You'll also want
to do the :ref:`push-all-versions` section.

.. tip::

    You may want to enable GitHub's `protected branches <https://help.github.com/articles/about-protected-branches/>`_
    feature for the gh-pages branch to prevent you or anyone from accidentally deleting the branch from remote.

This guide assumes:

1. You already have documentation in your master branch and SCVersioning builds it locally. If not you'll need to use
   the :option:`--root-ref` argument.
2. You already have your CI configured and running on your repo (this guide uses Travis CI but it should work on any
   other).

Turn Off Jekyll
===============

Building on the steps in the :ref:`tutorial` document you'll want to disable Jekyll because it doesn't copy over files
and directories `that start with underscores <https://github.com/blog/572-bypassing-jekyll-on-github-pages>`_, which
Sphinx uses.

.. code-block:: bash

    git checkout gh-pages
    git pull origin gh-pages
    touch .nojekyll
    git add .nojekyll
    git commit
    git push origin gh-pages
    git checkout master  # Or whatever branch you were in.

Then navigate to https://username.github.io/repo_name/ and if you used ``.`` for your :option:`REL_DEST` you should see
your HTML docs there. Otherwise if you used something like ``html/docs`` you'll need to navigate to
https://username.github.io/repo_name/html/docs/.

.. tip::

    Old repositories may not have **Enforce HTTPS** enabled for their GitHub Pages. It's a good idea to enable this
    feature. More info: https://help.github.com/articles/securing-your-github-pages-site-with-https/

Running in CI
=============

The goal of using GitHub Pages is to have docs automatically update on every new/changed branch/tag. In this example
we'll be using Travis CI but any CI should work.

Travis won't be able to push any changes to the gh-pages branch without SSH keys. This guide will worry about just
getting Travis to run SCVersioning. It should only fail when trying to push to origin.

CI Config File
--------------

Edit your CI configuration file (e.g. `.travis.yml <https://docs.travis-ci.com/user/customizing-the-build/>`_) with:

.. code-block:: yaml

    install:
      - pip install sphinxcontrib-versioning
    after_success:
      - git config --global user.email "builds@travis-ci.com"
      - git config --global user.name "Travis CI"
      - sphinx-versioning push docs gh-pages .

The two git config lines are needed to make commits locally to the gh-pages branch (cloned to a temporary directory by
SCVersioning). If you want SCVersioning to delete unrelated files from the gh-pages branch (e.g. deleted branches' HTML
documentation, deleted tags, etc) change the sphinx-versioning command to:

.. code-block:: bash

    sphinx-versioning -e .gitignore -e .nojekyll -e README.rst push docs gh-pages .

This tells SCVersioning to delete all files in gh-pages except those three. More information in :option:`--grm-exclude`.

Commit
------

Commit your changes to the CI config file and push. You should see documentation building successfully, but it should
fail when it tries to push since we haven't given your CI any permission to make changes to the git repository.

SSH Key
=======

Now that we know SCVersioning works fine locally and remotely it's time to unleash it. We'll be using
`Deploy Keys <https://developer.github.com/guides/managing-deploy-keys/>`_ to grant Travis write access to your
repository. At the time of this writing this is the most narrow-scoped authorization method for docs deployment.

To avoid leaking the SSH private key (thereby granting write access to the repo) we'll be using Travis CI's
`Encrypting Files <https://docs.travis-ci.com/user/encrypting-files/>`_ feature. You'll need to install the Travis CI
`ruby client <https://github.com/travis-ci/travis.rb#installation>`_ for this section.

ssh-keygen
----------

First we'll create the SSH key pair.

.. code-block:: bash

    ssh-keygen -t rsa -b 4096 -C "Travis CI Deploy Key" -N "" -f docs/key
    cat docs/key.pub  # We'll be adding this to GitHub's repo settings page.
    travis encrypt-file docs/key docs/key.enc --add after_success  # Updates .travis.yml
    rm docs/key docs/key.pub  # Don't need these anymore.

We need to give GitHub your SSH **public** key (the one we ran with ``cat``). Go to
https://github.com/username/repo_name/settings/keys and click "Add deploy key". The title could be anything (e.g.
"Travis CI Deploy Key"). The key you're pasting will be one long line and will look something like "ssh-rsa AAAAB3N...==
Travis CI Deploy Key"

Be sure to check **Allow write access**.

travis.yml
----------

The ``travis encrypt-file`` command should have updated your ``.travis.yml`` with the openssl command for you. However
we still need to make one more change to the file before committing it. Update .travis.yml to make the after_success
section look like this:

.. code-block:: bash

    after_success:
      - eval "$(ssh-agent -s)"; touch docs/key; chmod 0600 docs/key
      - openssl aes-256-cbc -d -K "$encrypted_key" -iv "$encrypted_iv" < docs/key.enc > docs/key
        && ssh-add docs/key  # Use && to prevent ssh-add from prompting during pull requests.
      - git config --global user.email "builds@travis-ci.com"
      - git config --global user.name "Travis CI"
      - git remote set-url --push origin "git@github.com:$TRAVIS_REPO_SLUG"
      - export ${!TRAVIS*}  # Optional, for commit messages.
      - sphinx-versioning push docs gh-pages .

.. warning::

    Always conditionally run ssh-add only if openssl succeeds like in the example above. Encrypted environment variables
    are not set on Travis CI and probably other CIs during pull requests for security reasons. If you always run ssh-add
    (which appears to be what everyone does) all of your pull requests will have failing tests because:

    #. Travis CI runs all commands in after_success even if one fails.
    #. openssl appears to copy "key.enc" to "key" when it fails to decrypt.
    #. ssh-add will prompt for a passphrase because it thinks the file is encrypted with an SSH passphrase.
    #. The Travis job will hang, timeout, and fail even if tests pass.

Finally commit both **.travis.yml** and the encrypted **docs/key.enc** file. Push and watch Travis update your docs
automatically for you.
