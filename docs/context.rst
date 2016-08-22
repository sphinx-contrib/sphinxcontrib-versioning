.. _context:

================
HTML Context API
================

The following Jinja2_ context variables are exposed in `the Sphinx HTML builder context <sphinx_context_>`_ in all
versions.

Versions Iterable
=================

``versions`` is the main variable of interest. It yields names of other (and the current) versions and relative URLs to
them. You can iterate on it to get all branches and tags, or use special properties attached to it to yield just
branches or just tags.

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

Functions
=========

.. function:: vhasdoc(other_version)

    Similar to Sphinx's `hasdoc() <sphinx_hasdoc_>`_ function. Returns True if the current document exists in another
    version.

    .. code-block:: jinja

        {% if vhasdoc('master') %}
            This doc is available in <a href="../master/index.html">master</a>.
        {% endif %}

.. function:: vpathto(other_version)

    Similar to Sphinx's `pathto() <sphinx_pathto_>`_ function. Has two behaviors:

    1. If the current document exists in the specified other version pathto() returns the relative URL to that document.
    2. If the current document does not exist in the other version the relative URL to that version's
       `master_doc <sphinx_master_doc_>`_ is returned instead.

    .. code-block:: jinja

        {% if vhasdoc('master') %}
            This doc is available in <a href="{{ vpathto('master') }}">master</a>.
        {% else %}
            Go to <a href="{{ vpathto('master') }}">master</a> for the latest docs.
        {% endif %}

Other Variables
===============

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

.. _Jinja2: http://jinja.pocoo.org/
.. _sphinx_context: http://www.sphinx-doc.org/en/stable/config.html?highlight=context#confval-html_context
.. _sphinx_hasdoc: http://www.sphinx-doc.org/en/stable/templating.html#hasdoc
.. _sphinx_master_doc: http://www.sphinx-doc.org/en/stable/config.html#confval-master_doc
.. _sphinx_pathto: http://www.sphinx-doc.org/en/stable/templating.html#pathto
