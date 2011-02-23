# -*- coding: utf-8 -*-
"""
To run the tests, first install the following packages:

    nose
    nosegae==0.1.7
    webtest
    gaetestbed
    coverage

Then run run_tests.py from the repository root.
"""
import os
import sys

import nose

# Explicitly defining to not cover tipfy.template.
cover_packages = [
    'tipfy.app',
    'tipfy.appengine',
    'tipfy.auth',
    'tipfy.config',
    'tipfy.debugger',
    'tipfy.dev',
    'tipfy.i18n',
    'tipfy.middleware',
    'tipfy.routing',
    'tipfy.manage',
    'tipfy.sessions',
    'tipfy.testing',
    'tipfy.utils',
    'tipfyext',
]

if __name__ == '__main__':
    base = os.path.abspath(os.path.dirname(__file__))
    tipfy = os.path.join(base, '..')
    app = os.path.join(base, 'project', 'app', 'lib', 'dist')
    gae = os.path.join(base, 'project', 'var', 'parts', 'google_appengine')
    sys.path[0:0] = [tipfy, app, gae]

    argv = [__file__]
    argv += '-d --with-gae -P --without-sandbox --with-coverage --cover-erase --gae-application=./project/app'.split()
    argv += ['--cover-package=%s' % ','.join(cover_packages)]
    nose.run(argv=argv)
