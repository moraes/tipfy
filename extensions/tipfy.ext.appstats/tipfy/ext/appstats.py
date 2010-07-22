# -*- coding: utf-8 -*-
"""
= tipfy.ext.appstats

Sets up the appstats [[middleware]]. Can be used either in production or
development.
"""
from google.appengine.ext.appstats.recording import appstats_wsgi_middleware


class AppstatsMiddleware(object):
    def post_make_app(self, app):
        """Wraps the application by App Engine's appstats.
        * Params: 
        ** **app**: The WSGI application instance.
        * Returns: 
        ** The application, wrapped or not.
        """
        # Wrap the callable, so we keep a reference to the app...
        app.wsgi_app = appstats_wsgi_middleware(app.wsgi_app)
        # ...and return the original app.
        return app