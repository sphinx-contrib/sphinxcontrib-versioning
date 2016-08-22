.. _banner:

==============
Banner Message
==============

Banner messages can be displayed at the top of every document informing users that they are currently viewing either old
or the development version of the project's documentation, with the exception of the :option:`--banner-main-ref`. This
feature is inspired by banner on the `Jinja2 documentation <http://jinja.pocoo.org/docs/dev/>`_.

The banner feature is disabled by default. It can be enabled with the :option:`--show-banner` setting.

.. figure:: screenshots/sphinx_rtd_theme_banner_dev.png
    :target: _images/sphinx_rtd_theme_banner_dev.png

    The message displayed when users are viewing docs from a branch and the :option:`--banner-main-ref` is a tag. The
    entire banner is a link that sends users to the latest version of the current page if it exists there.

.. figure:: screenshots/sphinx_rtd_theme_banner_old.png
    :target: _images/sphinx_rtd_theme_banner_old.png

    The message displayed when users are viewing docs from a tag and the :option:`--banner-main-ref` is a tag. Like the
    message above this one links users to the latest version of the current page.

.. figure:: screenshots/sphinx_rtd_theme_banner_nourl.png
    :target: _images/sphinx_rtd_theme_banner_nourl.png

    An example of a banner message from a page that does not exist in the :option:`--banner-main-ref` version. Since
    there is no page to link to this is just text informing the user that they're viewing the development version of the
    docs.
