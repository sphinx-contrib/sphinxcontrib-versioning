.. _themes:

================
Supported Themes
================

Below are screen shots of the supported built-in Sphinx themes. You can the "Versions" section in each screen shot on
sidebars.

HTML Context Variables (API)
============================

If you want to add support to another theme it's pretty easy. The following `Jinja2 <http://jinja.pocoo.org/>`_ context
variables are exposed:

.. attribute:: current_version

    A string of the current version being built. This will be the git ref name (e.g. a branch name or tag name).

    .. code-block:: jinja

        <h3>Current Version: {{ current_version }}</h3>

.. attribute:: scv_is_branch

    A boolean set to True if the current version being built is from a git branch.

.. attribute:: scv_is_greatest_tag

    A boolean set to True if the current version being built is:

    * From a git tag.
    * A valid semver-formatted name (e.g. v1.2.3).
    * The highest version number.

.. attribute:: scv_is_recent_branch

    A boolean set to True if the current version being built is a git branch and is the most recent commit out of just
    git branches.

.. attribute:: scv_is_recent_ref

    A boolean set to True if the current version being built is the most recent git commit (branch or tag).

.. attribute:: scv_is_recent_tag

    A boolean set to True if the current version being built is a git tag and is the most recent commit out of just git
    tags.

.. attribute:: scv_is_root

    A boolean set to True if the current version being built is in the web root (defined by :option:`--root-ref`).

.. attribute:: scv_is_tag

    A boolean set to True if the current version being built is from a git tag.

.. attribute:: versions

    An iterable that yields 2-item tuples of strings. The first item is the version (branch/tag) name while the second
    item is the relative path to the documentation for that version. The path is URL safe and takes into account HTML
    pages in sub directories.

    .. code-block:: jinja

        {%- for name, url in versions %}
            <li><a href="{{ url }}">{{ name }}</a></li>
        {%- endfor %}

.. attribute:: versions.branches

    The ``versions`` iterable has a **branches** property that itself yields versions in branches (filtering out git
    tags). The order is the same and it yields the same tuples.

    .. code-block:: jinja

        <dl>
            <dt>Branches</dt>
            {%- for name, url in versions.branches %}
            <dd><a href="{{ url }}">{{ name }}</a></dd>
            {%- endfor %}
        </dl>

.. attribute:: versions.tags

    The ``versions`` iterable also has a **tags** property that itself yields versions in tags (filtering out git
    branches). Just as the **branches** property the order is maintained and the yielded tuples are the same.

    .. code-block:: jinja

        <dl>
            <dt>Tags</dt>
            {%- for name, url in versions.tags %}
            <dd><a href="{{ url }}">{{ name }}</a></dd>
            {%- endfor %}
        </dl>

Screen Shots
============

Below are screen shots of the supported built-in themes.

.. figure:: screenshots/sphinx_rtd_theme.png
    :target: _images/sphinx_rtd_theme.png

    sphinx_rtd_theme

.. figure:: screenshots/alabaster.png
    :target: _images/alabaster.png

    alabaster

.. figure:: screenshots/classic.png
    :target: _images/classic.png

    classic

.. figure:: screenshots/nature.png
    :target: _images/nature.png

    nature

.. figure:: screenshots/sphinxdoc.png
    :target: _images/sphinxdoc.png

    sphinxdoc

.. figure:: screenshots/bizstyle.png
    :target: _images/bizstyle.png

    bizstyle

.. figure:: screenshots/pyramid.png
    :target: _images/pyramid.png

    pyramid

.. figure:: screenshots/traditional.png
    :target: _images/traditional.png

    traditional
