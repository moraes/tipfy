# -*- coding: utf-8 -*-
"""
    tipfy.utils.debugger
    ~~~~~~~~~~~~~~~~~~~~

    Debugger extension, to be used in development only.

    Applies monkeypatch for Werkzeug's interactive debugger to work with the
    development server.

    See http://dev.pocoo.org/projects/jinja/ticket/349

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
class DebuggerMiddleware(object):
    def pre_run_app(self, app):
        """Wraps the application by Werkzeug's debugger.

        :param app:
            The ``WSGIApplication`` instance.
        :return:
            The application, wrapped or not.
        """
        if app.config.get('tipfy', 'dev') is False:
            # In production, don't use the debugger.
            return app

        from tipfy.ext.debugger.app import get_debugged_app
        return get_debugged_app(app)
