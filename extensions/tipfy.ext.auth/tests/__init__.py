# -*- coding: utf-8 -*-
# ----------------------------------
# Setup path and tipfy.ext namespace
import os
import sys

CURR_PATH    = os.path.abspath(os.path.dirname(__file__))
TIPFY_PATH   = os.path.abspath(os.path.join(CURR_PATH, '..', '..', '..'))
APP_PATH     = os.path.join(TIPFY_PATH, 'buildout', 'app')
DB_PATH      = os.path.join(TIPFY_PATH, 'extensions', 'tipfy.ext.db')
SESSION_PATH = os.path.join(TIPFY_PATH, 'extensions', 'tipfy.ext.session')

for path in [TIPFY_PATH, APP_PATH, DB_PATH, SESSION_PATH]:
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
