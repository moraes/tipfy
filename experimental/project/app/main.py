# -*- coding: utf-8 -*-
"""WSGI app setup."""
import os
import sys

if 'lib' not in sys.path:
    # Add lib as primary libraries directory, with fallback to lib/dist
    # and optionally to lib/dist.zip, loaded using zipimport.
    sys.path[0:0] = ['lib', 'lib/dist', 'lib/dist.zip']

from tipfy import Tipfy
from config import config
from urls import rules


def enable_appstats(app):
    """Enables appstats middleware."""
    if debug:
        return

    from google.appengine.ext.appstats.recording import appstats_wsgi_middleware
    app.wsgi_app = appstats_wsgi_middleware(app.wsgi_app)


def enable_debugger(app):
    """Enables debugger middleware."""
    if not debug:
        return

    # This enables better debugging info for errors in Jinja2 templates.
    from google.appengine.tools.dev_appserver import HardenedModulesHook
    HardenedModulesHook._WHITE_LIST_C_MODULES += ['_ctypes', 'gestalt']
    # This enables the pretty interactive debugger.
    from tipfy.debugger import debugger_wsgi_middleware
    app.wsgi_app = debugger_wsgi_middleware(app.wsgi_app)


# Is this the development server?
debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

# Instantiate the application.
app = Tipfy(rules=rules, config=config, debug=debug)
enable_appstats(app)
enable_debugger(app)


def main():
    # Run the app.
    app.run()


if __name__ == '__main__':
    main()
