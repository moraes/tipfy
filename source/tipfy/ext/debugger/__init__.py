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


def set_debugger(app):
    """Adds Werkzeug's pretty debugger screen, via monkeypatch. This only works
    in the development server.

    TODO: this won't work if jinja2 is not available in lib, as it is used
    for the debugger templates.
    """
    global _debugged_app
    from werkzeug import DebuggedApplication
    if _debugged_app is None:
        _debugged_app = DebuggedApplication(app, evalex=True)
    return _debugged_app


def make_wsgi_app(config):
    """Creates a new `WSGIApplication` object and applies optional WSGI
    middlewares.
    """
    # Start the WSGI application.
    app = set_debugger(WSGIApplication(config))

    # Wrap the WSGI application so that cleaning up happens after request end.
    return local_manager.make_middleware(app)
