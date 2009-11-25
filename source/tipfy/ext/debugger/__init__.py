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


def before_app_run(app=None):
    """Middleware to wrap the application by Werkzeug's debugger."""
    global _debugged_app

    # Wrap app with the debugger.
    if _debugged_app is None:
        from werkzeug import DebuggedApplication
        _debugged_app = DebuggedApplication(app, evalex=True)

    return _debugged_app
