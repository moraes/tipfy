# -*- coding: utf-8 -*-
"""
    To run the tests:

    1. Install nose and nosegae

    2. Run nosetests in the tests dir, poiting to the application dir.
        Optionally you can define a temporary directory for the datastore used
        in the tests.

       $ nosetests --with-gae --gae-application=../source --gae-datastore=/path/to/test/datastore
"""
import sys
from os import path

app_path = path.abspath(path.join(path.dirname(__file__), '..', 'source'))
lib_path = path.join(app_path, 'lib')
sys.path.insert(0, lib_path)
sys.path.insert(0, app_path)

from tipfy import make_wsgi_app
import config

# Instantiate the application.
application = make_wsgi_app(config)
