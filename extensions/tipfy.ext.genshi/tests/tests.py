# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.genshi
"""
import os
import unittest

from tipfy import RequestHandler, Response, Tipfy
from tipfy.ext import genshi


current_dir = os.path.abspath(os.path.dirname(__file__))
templates_dir = os.path.join(current_dir, 'resources', 'templates')

HTML = """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <title>%(message)s</title>
    </head>
    <body>
        %(message)s
    </body>
</html>"""


class TestGenshi(unittest.TestCase):
    def setUp(self):
        Tipfy.request = Tipfy.request_class.from_values()

    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_render_template(self):
        genshi._environment = None
        app = Tipfy({'tipfy.ext.genshi': {'templates_dir': templates_dir}})

        message = 'Hello, World!'
        res = genshi.render_template('template1.html', _method='text', message=message)
        assert res == message + '\n'

    def test_render_template_html(self):
        genshi._environment = None
        app = Tipfy({'tipfy.ext.genshi': {'templates_dir': templates_dir}})

        message = 'Hello, World!'
        res = genshi.render_template('template3.html', message=message)
        assert res == HTML % {'message': message}

    def test_render_response(self):
        genshi._environment = None
        app = Tipfy({'tipfy.ext.genshi': {'templates_dir': templates_dir}})

        message = 'Hello, World!'
        response = genshi.render_response('template1.html', _method='text', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/plain'
        assert response.data == message + '\n'

    def test_render_response_no_method(self):
        genshi._environment = None
        app = Tipfy({'tipfy.ext.genshi': {'templates_dir': templates_dir}})

        message = 'Hello, World!'
        response = genshi.render_response('template2.txt', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/plain'
        assert response.data == message + '\n'

    def test_genshi_mixin_render_template(self):
        class MyHandler(RequestHandler, genshi.GenshiMixin):
            def __init__(self, app, request):
                self.app = app
                self.request = request
                self.context = {}

        app = Tipfy({'tipfy.ext.genshi': {'templates_dir': templates_dir}})
        message = 'Hello, World!'

        handler = MyHandler(Tipfy.app, Tipfy.request)
        response = handler.render_template('template1.html', _method='text', message=message)
        assert response == message + '\n'

    def test_genshi_mixin_render_response(self):
        class MyHandler(RequestHandler, genshi.GenshiMixin):
            def __init__(self, app, request):
                self.app = app
                self.request = request
                self.context = {}

        app = Tipfy({'tipfy.ext.genshi': {'templates_dir': templates_dir}})
        message = 'Hello, World!'

        handler = MyHandler(Tipfy.app, Tipfy.request)
        response = handler.render_response('template1.html', _method='text', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/plain'
        assert response.data == message + '\n'
