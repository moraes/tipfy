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

if __name__ == '__main__':
    base = os.path.abspath(os.path.dirname(__file__))
    tipfy = os.path.join(base, '..')
    app   = os.path.join(base, 'project', 'app', 'lib', 'dist')
    sys.path[0:0] = [tipfy, app]

    argv = [__file__]
    argv += '-d --with-gae -P --without-sandbox --cover-erase --with-coverage --cover-package=tipfy --gae-application=./project/app'.split()
    nose.run(argv=argv)
