.. _nfsn:

====================
NearlyFreeSpeech.NET
====================

This guide will go over how to host your built documentation on `NFSN <https://www.nearlyfreespeech.net/>`_. We'll be
using GitHub and Travis CI to actually build the docs and push them to NFSN but any other providers can be substituted.

We'll be covering two methods of having NFSN host your documentation: using ``rsync`` to transfer HTML files to NFSN and
using a remote git repository hosted on NFSN using ``git init --bare`` and having a git hook export HTML files to the
"/home/pubic" directory. Since NFSN's pricing structure is usage based the latter method technically costs more since
the entire git history of the HTML files' git branch will be stored on NFSN, whereas in the rsync method only the HTML
files are stored on NFSN. The cost difference is probably minimal but it's something to keep in mind.

Before starting be sure to go through the :ref:`tutorial` first to make sure you can build your docs locally. If you're
going with the ``rsync`` route you can stop after the :ref:`build-all-versions` section. Otherwise you should go through
the :ref:`push-all-versions` section as well.

This guide assumes:

1. You already have documentation in your master branch and SCVersioning builds it locally. If not you'll need to use
   the :option:`--root-ref` argument.
2. You already have Travis CI configured and running on your repo.
3. You already have an account on NFSN.

Running in CI
=============

Before touching NFSN let's setup Travis CI to run SCVersioning. Edit your
`.travis.yml <https://docs.travis-ci.com/user/customizing-the-build/>`_ file with:

.. code-block:: yaml

    addons:
      ssh_known_hosts: ssh.phx.nearlyfreespeech.net
    install:
      - pip install sphinxcontrib-versioning
    after_success:
      - sphinx-versioning build docs docs/_build/html

Commit your changes and push. You should see documentation building successfully.

SSH Key
-------

Now we need to create an SSH key pair and upload the private key to Travis CI. The public key will be given to NFSN in
the next section.

To avoid leaking the SSH private key (thereby granting write access to the repo) we'll be using Travis CI's
`Encrypting Files <https://docs.travis-ci.com/user/encrypting-files/>`_ feature. You'll need to install the Travis CI
`ruby client <https://github.com/travis-ci/travis.rb#installation>`_ for this section.

Create the SSH key pair.

.. code-block:: bash

    ssh-keygen -t rsa -b 4096 -C "Travis CI Deploy Key" -N "" -f docs/key
    cat docs/key.pub  # We'll be adding this to NFSN's Add SSH Key page.
    travis encrypt-file docs/key docs/key.enc --add after_success  # Updates .travis.yml
    rm docs/key docs/key.pub  # Don't need these anymore.

The ``travis encrypt-file`` command should have updated your ``.travis.yml`` with the openssl command for you. However
we still need to make one more change to the file before committing it. Update .travis.yml to make the after_success
section look like the following. Remember to replace **$encrypted_x_key** and **$encrypted_x_iv** with what you
currently have.

.. code-block:: yaml

    after_success:
      - eval "$(ssh-agent -s)"; touch docs/key; chmod 0600 docs/key
      - openssl aes-256-cbc -d -K $encrypted_x_key -iv $encrypted_x_iv < docs/key.enc > docs/key
        && ssh-add docs/key  # Use && to prevent ssh-add from prompting during pull requests.
      - sphinx-versioning build docs docs/_build/html

.. warning::

    Always conditionally run ssh-add only if openssl succeeds like in the example above. Encrypted environment variables
    are not set on Travis CI and probably other CIs during pull requests for security reasons. If you always run ssh-add
    (which appears to be what everyone does) all of your pull requests will have failing tests because:

    #. Travis CI runs all commands in after_success even if one fails.
    #. openssl appears to copy "key.enc" to "key" when it fails to decrypt.
    #. ssh-add will prompt for a passphrase because it thinks the file is encrypted with an SSH passphrase.
    #. The Travis job will hang, timeout, and fail even if tests pass.

Finally commit both **.travis.yml** and the encrypted **docs/key.enc** file.

Create an NFSN Site
===================

First we'll create a static site on NFSN. Even if you've been using NFSN it's a good idea to try this out in a dedicated
and disposable site to avoid breaking anything important.

1. Go to the **sites** tab in the member portal and click "Create a New Site". This guide will use **scversioning** as
   the new site's short name.
2. Since this is all just static HTML files you won't need PHP/MySQL/etc. Select the "Static Content" server type.
3. You should be able to visit `http://scversioning.nfshost.com/` and get an HTTP 403 error.
4. Go to the **profile** tab and click "Add SSH Key". The key you're pasting will be one long line and will look
   something like "ssh-rsa AAAAB3N...== Travis CI Deploy Key"

Pushing From CI to NFSN
=======================

This is the moment of truth. You need to decide if you want to just rsync HTML files from Travis CI to NFSN or add NFSN
as a git remote, have SCVersioning push to NFSN, and let a git hook on NFSN move HTML files to the web root.

Using Rsync
-----------

This is simpler and costs less (though probably not by much since NFSN is pretty cheap). All you need to do is add these
lines to your .travis.yml file's ``after_success`` section. Be sure to replace username_scversioning with your
actual username and remove the previous sphinx-versioning line.

.. code-block:: yaml

    - export destination=username_scversioning@ssh.phx.nearlyfreespeech.net:/home/public
    - sphinx-versioning build docs docs/_build/html && rsync -icrz --delete docs/_build/html/ $destination

We're adding rsync to the same line as sphinx-versioning because Travis CI runs all commands in after_success even if
one of them fails. No point in rsyncing if sphinx-versioning fails.

After committing you should see Travis CI rsync HTML files to NFSN and your site should be up and running with your
documentation.

Using Git Bare Repo
-------------------

You can take advantage of SCVersioning's git push retry logic if you go this route. Here we'll be pushing build docs to
the ``nfsn-pages`` branch on the remote repo located in your NFSN's private home directory.

First create the remote repo on NFSN. SSH into your new site and run these commands:

.. code-block:: bash

    mkdir /home/private/repo
    cd /home/private/repo
    git init --bare
    touch hooks/post-receive
    chmod +x hooks/post-receive

Next setup the post-receive git hook. Write the following to **/home/private/repo/hooks/post-receive** on NFSN:

.. code-block:: bash

    # !/bin/bash
    export GIT_WORK_TREE="/home/public"
    while read sha1old sha1new refname; do
        branch=$(git rev-parse --symbolic --abbrev-ref $refname)
        [ "$branch" != "nfsn-pages" ] && continue
        lockf -k -t5 /home/tmp/nfsn_pages.lock git checkout -f $branch
    done

Now before we move on to the final step you'll need to create the initial commit to the nfsn-pages branch on the NFSN
remote. SCVersioning does not create new branches, they must previously exist on the remote. Here we'll be renaming the
``gh-pages`` branch you created in :ref:`pushing-to-remote-branch` to ``nfsn-pages`` and pushing it to our new NFSN
remote repo. Run these commands on your local machine (replace username_scversioning with your actual username):

.. code-block:: bash

    git push origin --delete gh-pages  # No longer need this in origin.
    git checkout gh-pages
    git branch -m nfsn-pages
    git remote add nfsn "username_scversioning@ssh.phx.nearlyfreespeech.net:/home/private/repo"
    git push nfsn nfsn-pages

At this point you should see .gitignore and README.rst in your /home/public directory on NFSN. Finally add these lines
to your .travis.yml file's ``after_success`` section. Be sure to replace username_scversioning with your actual username
and remove the previous sphinx-versioning line.

.. code-block:: yaml

    - git config --global user.email "builds@travis-ci.com"
    - git config --global user.name "Travis CI"
    - git remote add nfsn "username_scversioning@ssh.phx.nearlyfreespeech.net:/home/private/repo"
    - export ${!TRAVIS*}  # Optional, for commit messages.
    - sphinx-versioning push -P nfsn docs nfsn-pages .

After committing you should see Travis CI push HTML files to NFSN and your site should be up and running with your
documentation.
