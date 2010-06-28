# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.mako
"""
import os
import unittest

from tipfy import RequestHandler, Response, Tipfy
from tipfy.ext import mako


current_dir = os.path.abspath(os.path.dirname(__file__))
templates_dir = os.path.join(current_dir, 'resources', 'templates')


class TestMako(unittest.TestCase):
    def setUp(self):
        Tipfy.request = Tipfy.request_class.from_values()

    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_get_lookup(self):
        app = Tipfy({'tipfy.ext.mako': {'templates_dir': templates_dir}})
        assert isinstance(mako.get_lookup(), mako.TemplateLookup)

    def test_render_template(self):
        app = Tipfy({'tipfy.ext.mako': {'templates_dir': templates_dir}})
        message = 'Hello, World!'
        res = mako.render_template('template1.html', message=message)
        assert res == message + '\n'

    def test_render_response(self):
        app = Tipfy({'tipfy.ext.mako': {'templates_dir': templates_dir}})

        message = 'Hello, World!'
        response = mako.render_response('template1.html', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/html'
        assert response.data == message + '\n'

    def test_mako_mixin_render_template(self):
        class MyHandler(RequestHandler, mako.MakoMixin):
            def __init__(self, app, request):
                self.app = app
                self.request = request
                self.context = {}

        app = Tipfy({'tipfy.ext.mako': {'templates_dir': templates_dir}})
        message = 'Hello, World!'

        handler = MyHandler(Tipfy.app, Tipfy.request)
        response = handler.render_template('template1.html', message=message)
        assert response == message + '\n'

    def test_mako_mixin_render_response(self):
        class MyHandler(RequestHandler, mako.MakoMixin):
            def __init__(self, app, request):
                self.app = app
                self.request = request
                self.context = {}

        app = Tipfy({'tipfy.ext.mako': {'templates_dir': templates_dir}})
        message = 'Hello, World!'

        handler = MyHandler(Tipfy.app, Tipfy.request)
        response = handler.render_response('template1.html', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/html'
        assert response.data == message + '\n'
