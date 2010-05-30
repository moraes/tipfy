# -*- coding: utf-8 -*-
"""
To run the tests, first install the following packages:

    easy_install nose
    easy_install nosegae==0.1.7
    easy_install webtest
    easy_install gaetestbed
    easy_install coverage

Then run the tests from the repository root:

    nosetests -d --with-gae --without-sandbox --cover-erase --with-coverage --cover-package=tipfy --gae-application=./buildout/app
"""
# ----------------------------------
# Setup path and tipfy.ext namespace
import os
import sys

CURR_PATH  = os.path.abspath(os.path.dirname(__file__))
TIPFY_PATH = os.path.abspath(os.path.join(CURR_PATH, '..'))
APP_PATH   = os.path.join(TIPFY_PATH, 'buildout', 'app')

paths = [TIPFY_PATH, APP_PATH]

for ext in ['auth', 'db', 'i18n', 'jinja2', 'session']:
    paths.append(os.path.join(TIPFY_PATH, 'extensions', 'tipfy.ext.' + ext))

for path in paths:
    if path not in sys.path:
        sys.path.insert(0, path)

__import__('pkg_resources').declare_namespace('tipfy.ext')

def setup():
    if 'handlers' in sys.modules:
        del sys.modules['handlers']

    sys.path.insert(0, CURR_PATH)

def teardown():
    if CURR_PATH in sys.path:
        sys.path.remove(CURR_PATH)
