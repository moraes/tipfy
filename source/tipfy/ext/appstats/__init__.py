# -*- coding: utf-8 -*-
"""
    tipfy.ext.appstats
    ~~~~~~~~~~~~~~~~~~

    Sets up the appstats middleware. Can be used either in production or
    development.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from google.appengine.ext.appstats.recording import appstats_wsgi_middleware


class AppstatsMiddleware(object):
    def pre_run_app(self, app):
        """Wraps the application by by AppEngine's appstats

        :param app:
            The ``WSGIApplication`` instance.
        :return:
            The application, wrapped or not.
        """
        return appstats_wsgi_middleware(app)