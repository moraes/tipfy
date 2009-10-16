# -*- coding: utf-8 -*-
"""
    tipfy.utils.debug
    ~~~~~~~~~~~~~~~~~

    Monkey patch to make Werkeug's debugger work in App Engine.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
import sys
from os.path import join, dirname
from jinja2 import Environment, FileSystemLoader

from tipfy import local_manager, WSGIApplication

import inspect
inspect.getsourcefile = inspect.getfile

# Application wrapped by the debugger. Only set in development.
_debugged_app = None

env = Environment(loader=FileSystemLoader([join(dirname(__file__),
    'templates')]))

def get_template(filename):
    return env.get_template(filename)


def render_template(template_filename, **context):
    return get_template(template_filename).render(**context)


def set_debugger(app):
    """Adds Werkzeug's pretty debugger screen, via monkeypatch. This only works
    in the development server.

    TODO: this won't work if jinja2 is not available in lib, as it is used
    for the debugger templates.
    """
    global _debugged_app
    sys.modules['werkzeug.debug.utils'] = sys.modules[__name__]
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
