# -*- coding: utf-8 -*-
"""
    tipfy.utils.debugger
    ~~~~~~~~~~~~~~~~~~~~

    Debugger extension, to be used in development only.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
# Apply patches to make the debugger fully work on development server.
import tipfy.ext.debugger.patch

# Application wrapped by the debugger.
_debugged_app = None


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
