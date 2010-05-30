# -*- coding: utf-8 -*-
# ----------------------------------
# Setup path and tipfy.ext namespace
import os
import sys

TIPFY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
    '..', '..'))
APP_PATH   = os.path.join(TIPFY_PATH, 'buildout', 'app')
DB_PATH    = os.path.join(TIPFY_PATH, 'extensions', 'tipfy.ext.db')

for path in [TIPFY_PATH, APP_PATH, DB_PATH]:
    if path not in sys.path:
        sys.path.insert(0, path)

__import__('pkg_resources').declare_namespace('tipfy.ext')

def setup():
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def teardown():
    path = os.path.abspath(os.path.dirname(__file__))
    if path in sys.path:
        sys.path.remove(path)
