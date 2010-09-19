# -*- coding: utf-8 -*-
import os
import sys

if 'lib' not in sys.path:
    # Add /lib as primary libraries directory, with fallback to /distlib
    # and optionally to distlib loaded using zipimport.
    sys.path[0:0] = ['lib', 'distlib', 'distlib.zip']

from tipfy import Tipfy
from config import config
from urls import rules

# Is this the development server?
debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

# Instantiate the application.
app = Tipfy(rules=rules, config=config, debug=debug)


def main():
    # Run the app!
    app.run()


if __name__ == '__main__':
    main()
