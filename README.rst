========================
sphinxcontrib-versioning
========================

Sphinx extension that allows building versioned docs for self-hosting.

* Python 2.7, 3.3, 3.4, and 3.5 supported on Linux and OS X.
* Python 2.7, 3.3, 3.4, and 3.5 supported on Windows (both 32 and 64 bit versions of Python).

📖 Full documentation: https://sphinxcontrib-versioning.readthedocs.io

.. image:: https://readthedocs.org/projects/sphinxcontrib-versioning/badge/?version=latest
    :target: https://sphinxcontrib-versioning.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/appveyor/ci/Robpol86/sphinxcontrib-versioning/master.svg?style=flat-square&label=AppVeyor%20CI
    :target: https://ci.appveyor.com/project/Robpol86/sphinxcontrib-versioning
    :alt: Build Status Windows

.. image:: https://img.shields.io/travis/sphinx-contrib/sphinxcontrib-versioning/master.svg?style=flat-square&label=Travis%20CI
    :target: https://travis-ci.org/sphinx-contrib/sphinxcontrib-versioning
    :alt: Build Status

.. image:: https://img.shields.io/codecov/c/github/sphinx-contrib/sphinxcontrib-versioning/master.svg?style=flat-square&label=Codecov
    :target: https://codecov.io/gh/sphinx-contrib/sphinxcontrib-versioning
    :alt: Coverage Status

.. image:: https://img.shields.io/pypi/v/sphinxcontrib-versioning.svg?style=flat-square&label=Latest
    :target: https://pypi.python.org/pypi/sphinxcontrib-versioning
    :alt: Latest Version

Quickstart
==========

Install:

.. code:: bash

    pip install sphinxcontrib-versioning

Usage:

.. code:: bash

    sphinx-versioning --help
    sphinx-versioning build --help
    sphinx-versioning push --help

.. changelog-section-start

Changelog
=========

This project adheres to `Semantic Versioning <http://semver.org/>`_.

2.2.1 - 2016-12-10
------------------

Added
    * Time value of ``html_last_updated_fmt`` will be the last git commit (authored) date.

Fixed
    * Unhandled KeyError exception when banner main ref fails pre-build.
    * https://github.com/sphinx-contrib/sphinxcontrib-versioning/issues/26
    * https://github.com/sphinx-contrib/sphinxcontrib-versioning/issues/27

2.2.0 - 2016-09-15
------------------

Added
    * Windows support.

Fixed
    * https://github.com/sphinx-contrib/sphinxcontrib-versioning/issues/17
    * https://github.com/sphinx-contrib/sphinxcontrib-versioning/issues/3

2.1.4 - 2016-09-03
------------------

Fixed
    * banner.css being overridden by conf.py: https://github.com/sphinx-contrib/sphinxcontrib-versioning/issues/23

2.1.3 - 2016-08-24
------------------

Fixed
    * Stopped blocking users from overriding their layout.html. Using another approach to inserting the banner.

2.1.2 - 2016-08-24
------------------

Fixed
    * Cloning from push remote instead of origin. If HTML files are pushed to another repo other than origin it doesn't
      make sense to clone from origin (previous files won't be available).

2.1.1 - 2016-08-23
------------------

Added
    * Command line option: ``--push-remote``

Fixed
    * Copy all remotes from the original repo to the temporarily cloned repo when pushing built docs to a remote.
      Carries over all remote URLs in case user defines a different URL for push vs fetch.

2.1.0 - 2016-08-22
------------------

Added
    * Option to enable warning banner in old/development versions. Similar to Jinja2's documentation.
    * Command line options: ``--banner-greatest-tag`` ``--banner-recent-tag`` ``--show-banner`` ``--banner-main-ref``
    * Jinja2 context functions: ``vhasdoc()`` ``vpathto()``
    * Jinja2 context variables: ``scv_show_banner`` ``scv_banner_greatest_tag`` ``scv_banner_main_ref_is_branch``
      ``scv_banner_main_ref_is_tag`` ``scv_banner_main_version`` ``scv_banner_recent_tag``

Changed
    * Root ref will also be built in its own directory like other versions. All URLs to root ref will point to the one
      in that directory instead of the root. More info: https://github.com/sphinx-contrib/sphinxcontrib-versioning/issues/15
    * Renamed Jinja2 context variable ``scv_is_root_ref`` to ``scv_is_root``.

Fixed
    * https://github.com/sphinx-contrib/sphinxcontrib-versioning/issues/13
    * https://github.com/sphinx-contrib/sphinxcontrib-versioning/pull/20

Removed
    * Jinja2 context variables: ``scv_root_ref_is_branch`` ``scv_root_ref_is_tag``

2.0.0 - 2016-08-15
------------------

Added
    * ``--git-root`` command line option.
    * ``--whitelist-branches`` and ``--whitelist-tags`` command line options.
    * ``--local-conf`` and ``--no-local-conf`` command line options.
    * Load settings from **conf.py** file and command line arguments instead of just the latter.

Changed
    * Renamed command line option ``--prioritize`` to ``--priority``.
    * Renamed command line option ``-S`` to ``-s``.
    * ``--chdir``, ``--no-colors``, and ``--verbose`` must be specified before build/push and the other after.
    * ``--sort`` no longer takes a comma separated string. Now specify multiple times (like ``--grm-exclude``).
    * Renamed ``--sort`` value "chrono" to "time".
    * Reordered positional command line arguments. Moved ``REL_SOURCE`` before the destination arguments.
    * Renamed command line option ``-C`` to ``-N`` for consistency with sphinx-build.

Fixed
    * Exposing sphinx-build verbosity to SCVersioning. Specify one ``-v`` to make SCVersioning verbose and two or more
      to make sphinx-build verbose.
    * Using ``--no-colors`` also turns off colors from sphinx-build.
    * https://github.com/sphinx-contrib/sphinxcontrib-versioning/issues/16

1.1.0 - 2016-08-07
------------------

Added
    * Exposing Jinja2 context variables: ``scv_is_branch`` ``scv_is_root_ref`` ``scv_is_tag`` ``scv_root_ref_is_branch``
      ``scv_root_ref_is_tag`` ``scv_is_greatest_tag`` ``scv_is_recent_branch`` ``scv_is_recent_ref``
      ``scv_is_recent_tag``

Changed
    * Version links point to that version of the current page if it exists there.

Fixed
    * https://github.com/sphinx-contrib/sphinxcontrib-versioning/issues/5

1.0.1 - 2016-08-02
------------------

Fixed
    * easy_install: https://github.com/sphinx-contrib/sphinxcontrib-versioning/issues/4

1.0.0 - 2016-07-23
------------------

* Initial release.

.. changelog-section-end
