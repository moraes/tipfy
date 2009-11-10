# -*- coding: utf-8 -*-
"""
    To run the tests:

    1. Download GAEUnit from http://code.google.com/p/gaeunit/

    2. Add (or symlink) gaeunit.py to the app directory.

    3. Add (or symlink) the /test dir to the app directory.

    4. Add ther test URL to app.yaml (use login:admin to disallow acces in case
       it is deployed by accident):

       - url: /test.*
         script: gaeunit.py
         login: admin

    5. Start the dev server and access in a browser:

       http://localhost:8080/test
"""
import sys
if 'lib' not in sys.path:
    sys.path.insert(0, 'lib')


def get_app():
    from tipfy import make_wsgi_app
    import config
    # Need to reload the urls module to unbind rules.
    # Better would be to wrap the rules by a function...
    reload(__import__('urls'))
    return make_wsgi_app(config)


def get_environ(*args, **kwargs):
    from os import environ
    from werkzeug.test import create_environ
    path = kwargs.get('path', '/')
    if 'base_url' not in kwargs:
        kwargs['base_url'] = 'http://%s%s' % (environ['HTTP_HOST'], path)

    return create_environ(*args, **kwargs)


def get_request(environ):
    from werkzeug import Request
    return Request(environ)


def get_response():
    from werkzeug import Response
    return Response()
