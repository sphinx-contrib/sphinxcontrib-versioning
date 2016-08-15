========================
sphinxcontrib-versioning
========================

Sphinx extension that allows building versioned docs for self-hosting.

* Python 2.7, 3.3, 3.4, and 3.5 supported on Linux and OS X.

📖 Full documentation: https://robpol86.github.io/sphinxcontrib-versioning

.. image:: https://img.shields.io/travis/Robpol86/sphinxcontrib-versioning/master.svg?style=flat-square&label=Travis%20CI
    :target: https://travis-ci.org/Robpol86/sphinxcontrib-versioning
    :alt: Build Status

.. image:: https://img.shields.io/coveralls/Robpol86/sphinxcontrib-versioning/master.svg?style=flat-square&label=Coveralls
    :target: https://coveralls.io/github/Robpol86/sphinxcontrib-versioning
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
    * https://github.com/Robpol86/sphinxcontrib-versioning/issues/16

1.1.0 - 2016-08-07
------------------

Added
    * Exposing Jinja2 context variables: ``scv_is_branch`` ``scv_is_root_ref`` ``scv_is_tag`` ``scv_root_ref_is_branch``
      ``scv_root_ref_is_tag`` ``scv_is_greatest_tag`` ``scv_is_recent_branch`` ``scv_is_recent_ref``
      ``scv_is_recent_tag``

Changed
    * Version links point to that version of the current page if it exists there.

Fixed
    * https://github.com/Robpol86/sphinxcontrib-versioning/issues/5

1.0.1 - 2016-08-02
------------------

Fixed
    * easy_install: https://github.com/Robpol86/sphinxcontrib-versioning/issues/4

1.0.0 - 2016-07-23
------------------

* Initial release.

.. changelog-section-end
