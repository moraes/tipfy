# -*- coding: utf-8 -*-
"""
    tipfy.ext.appstats
    ~~~~~~~~~~~~~~~~~~~~

    Sets up the appstats middleware.  Can be used either in production or
    development.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
def setup(app):
    """
    Setup this extension. It wraps the application by AppEngine's appstats
    middleware.

    To enable it, add this module to the list of extensions in ``config.py``:

    .. code-block:: python

       config = {
           'tipfy': {
               'extensions': [
                   'tipfy.ext.appstats',
                   # ...
               ],
           },
       }

    :param app:
        The WSGI application instance.
    :return:
        ``None``.
    """
    from google.appengine.ext.appstats.recording import appstats_wsgi_middleware
    app.hooks.add('pre_run_app', appstats_wsgi_middleware)