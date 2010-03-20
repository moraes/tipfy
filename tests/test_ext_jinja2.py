# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.jinja2
"""
import os
import unittest

from _base import get_environ

import tipfy
from tipfy.ext import jinja2

current_dir = os.path.abspath(os.path.dirname(__file__))
templates_dir = os.path.join(current_dir, 'files', 'jinja2')


class TestJinja2(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_render_template(self):
        app = tipfy.WSGIApplication({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})
        tipfy.local.request = tipfy.Request(get_environ())

        message = 'Hello, World!'
        res = jinja2.render_template('template1.html', message=message)
        assert res == message

    def test_render_response(self):
        app = tipfy.WSGIApplication({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})
        tipfy.local.request = tipfy.Request(get_environ())
        tipfy.local.response = tipfy.Response()

        message = 'Hello, World!'
        response = jinja2.render_response('template1.html', message=message)
        assert isinstance(response, tipfy.Response)
        assert response.mimetype == 'text/html'
        assert response.data == message
