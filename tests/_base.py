# -*- coding: utf-8 -*-
"""
  easy_install nose
  easy_install nose-gae
  easy_install webtest
  easy_install gaetestbed

  nosetests --with-gae --without-sandbox --gae-application=/path/to/source/
"""
import os, sys
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
    'source'))
LIBS_PATH = os.path.join(ROOT_PATH, 'lib')
if ROOT_PATH not in sys.path:
    sys.path.insert(0, LIBS_PATH)
    sys.path.insert(0, ROOT_PATH)


def get_app():
    from tipfy import make_wsgi_app
    import config
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
