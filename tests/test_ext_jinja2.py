# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.jinja2
"""
import os
import unittest

import _base

from tipfy import cleanup_wsgi_app, local, Response, WSGIApplication
from tipfy.ext import jinja2

current_dir = os.path.abspath(os.path.dirname(__file__))
templates_dir = os.path.join(current_dir, 'files', 'jinja2')
templates_compiled_target = os.path.join(current_dir, 'files', 'jinja2_compiled')


class TestJinja2(unittest.TestCase):
    def tearDown(self):
        cleanup_wsgi_app()

    def test_render_template(self):
        jinja2._environment = None
        app = WSGIApplication({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})

        message = 'Hello, World!'
        res = jinja2.render_template('template1.html', message=message)
        assert res == message

    def test_render_response(self):
        jinja2._environment = None
        app = WSGIApplication({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})

        message = 'Hello, World!'
        response = jinja2.render_response('template1.html', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/html'
        assert response.data == message

    def test_render_response_force_compiled(self):
        jinja2._environment = None
        app = WSGIApplication({'tipfy.ext.jinja2': {
            'templates_compiled_target': templates_compiled_target,
            'force_use_compiled': True,
        }})

        message = 'Hello, World!'
        response = jinja2.render_response('template1.html', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/html'
        assert response.data == message

    def test_jinja2_mixin(self):
        jinja2._environment = None
        class MyHandler(jinja2.Jinja2Mixin):
            def __init__(self):
                self.context = {}

        app = WSGIApplication({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})
        message = 'Hello, World!'

        handler = MyHandler()
        response = handler.render_response('template1.html', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/html'
        assert response.data == message

    def test_get_template_attribute(self):
        jinja2._environment = None
        app = WSGIApplication({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})

        hello = jinja2.get_template_attribute('hello.html', 'hello')
        assert hello('World') == 'Hello, World!'
