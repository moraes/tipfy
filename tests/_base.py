# -*- coding: utf-8 -*-
"""
To run the tests, first install the following packages:

    easy_install nose
    easy_install nosegae==0.1.7
    easy_install webtest
    easy_install gaetestbed
    easy_install coverage

Then run the tests from the repository root:

    nosetests -d --with-gae --without-sandbox --with-coverage --cover-package=tipfy --gae-application=./source/
"""
import os, sys
APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
    'source'))
LIB_PATH = os.path.join(APP_PATH, 'lib')
if APP_PATH not in sys.path:
    sys.path.insert(0, LIB_PATH)
    sys.path.insert(0, APP_PATH)


def get_app(config=None):
    from tipfy import make_wsgi_app
    if config is None:
        import config
        config = config.config

    return make_wsgi_app(config)


def get_environ(*args, **kwargs):
    from os import environ
    from werkzeug.test import create_environ
    path = kwargs.get('path', '/')
    if 'base_url' not in kwargs:
        kwargs['base_url'] = 'http://%s%s' % (environ.get('HTTP_HOST',
            'localhost:8080'), path)

    return create_environ(*args, **kwargs)


def get_request(environ):
    from werkzeug import Request
    return Request(environ)


def get_response():
    from werkzeug import Response
    return Response()
