# -*- coding: utf-8 -*-
# ----------------------------------
# Setup path and tipfy.ext namespace
import os
import sys

CURR_PATH  = os.path.abspath(os.path.dirname(__file__))
TIPFY_PATH = os.path.abspath(os.path.join(CURR_PATH, '..', '..', '..'))
APP_PATH   = os.path.join(TIPFY_PATH, 'buildout', 'app')

for path in [TIPFY_PATH, APP_PATH]:
    if path not in sys.path:
        sys.path.insert(0, path)

__import__('pkg_resources').declare_namespace('tipfy.ext')

def setup():
    sys.path.insert(0, CURR_PATH)

def teardown():
    if CURR_PATH in sys.path:
        sys.path.remove(CURR_PATH)
