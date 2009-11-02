# -*- coding: utf-8 -*-
"""
    tipfy.utils.debug
    ~~~~~~~~~~~~~~~~~

    Monkey patch to make Werkeug's debugger work in App Engine.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from tipfy import local_manager, WSGIApplication
# Apply debugger patches.
import tipfy.ext.debugger.patch

# Application wrapped by the debugger. Only set in development.
_debugged_app = None


def make_wsgi_app(config):
    """Creates a new `WSGIApplication` object and applies optional WSGI
    middlewares.
    """
    global _debugged_app

    # Start the WSGI application.
    app = WSGIApplication(config)

    # Wrap app with the debugger.
    if _debugged_app is None:
        from werkzeug import DebuggedApplication
        _debugged_app = DebuggedApplication(app, evalex=True)

    # Wrap the WSGI application so that cleaning up happens after request end.
    return local_manager.make_middleware(_debugged_app)
