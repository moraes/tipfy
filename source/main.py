# -*- coding: utf-8 -*-
"""
    main
    ~~~~

    Run Tipfy apps.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""
import sys
if 'lib' not in sys.path:
    sys.path.insert(0, 'lib')

import config
import tipfy

# Instantiate the application.
application = tipfy.make_wsgi_app(config.config)

# Issue 772 - http://code.google.com/p/googleappengine/issues/detail?id=772.
# We must keep this here until it is fixed in the dev server.
ultimate_sys_path = None
def fix_sys_path():
    global ultimate_sys_path
    if ultimate_sys_path is None:
        ultimate_sys_path = list(sys.path)
    else:
        if sys.path != ultimate_sys_path:
            sys.path[:] = ultimate_sys_path

# Run, and done!
def main():
    if tipfy.config['dev']:
        fix_sys_path()

    tipfy.run_wsgi_app(application)

if __name__ == '__main__':
    main()
