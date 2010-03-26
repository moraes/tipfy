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
import sys
from os.path import join, dirname
from jinja2 import Environment, FileSystemLoader

# Patch utils to use Jinja templates instead.
sys.modules['werkzeug.debug.utils'] = sys.modules[__name__]

# Application wrapped by the debugger.
_debugged_app = None

env = Environment(loader=FileSystemLoader([join(dirname(__file__),
    'templates')]))


# werkzeug.debug.utils
def get_template(filename):
    return env.get_template(filename)


def render_template(template_filename, **context):
    return get_template(template_filename).render(**context)


def setup(app):
    """
    Setup this extension. It wraps the application by Werkzeug's debugger.

    To enable it, add this module to the list of extensions in ``config.py``:

    .. code-block:: python

       config = {
           'tipfy': {
               'extensions': [
                   'tipfy.ext.debugger',
                   # ...
               ],
           },
       }

    :param app:
        The WSGI application instance.
    :return:
        ``None``.
    """
    if app.config.get('tipfy', 'dev') is True:
        app.hooks.add('pre_run_app', set_debugger)


def set_debugger(app):
    global _debugged_app

    # Wrap app with the debugger.
    if _debugged_app is None:
        from werkzeug import DebuggedApplication
        _debugged_app = DebuggedApplication(app, evalex=True)

    return _debugged_app
