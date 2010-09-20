# -*- coding: utf-8 -*-
"""WSGI app setup."""
import os
import sys

if 'lib' not in sys.path:
    # Add lib as primary libraries directory, with fallback to lib/dist
    # and optionally to lib/dist.zip, loaded using zipimport.
    sys.path[0:0] = [
        'lib',
        os.path.join('lib', 'dist'),
        os.path.join('lib', 'dist.zip'),
    ]

from tipfy import Tipfy
from config import config
from urls import rules

# Is this the development server?
debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

# Instantiate the application.
app = Tipfy(rules=rules, config=config, debug=debug)

if debug:
    # Enable debugger middleware.
    from tipfy.debugger import debugger_wsgi_middleware
    app.wsgi_app = debugger_wsgi_middleware(app.wsgi_app)


def main():
    # Run the app.
    app.run()


if __name__ == '__main__':
    main()
