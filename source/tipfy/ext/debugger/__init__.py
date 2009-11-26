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


def set_debugger(app=None):
    """Application hook executed right before the WSGI app runs.

    It wraps the application by Werkzeug's debugger.

    To enable it, add a hook to the list of hooks in ``config.py``:

    .. code-block:: python

       config = {
           'tipfy': {
               'hooks': {
                   'pre_run_app': ['tipfy.ext.debugger:set_debugger'],
                   # ...
               },
           },
       }

    :param app:
        A :class:`tipfy.WSGIApplication` instance.
    :return:
        ``None``.
    """
    global _debugged_app

    # Wrap app with the debugger.
    if _debugged_app is None:
        from werkzeug import DebuggedApplication
        _debugged_app = DebuggedApplication(app, evalex=True)

    return _debugged_app
