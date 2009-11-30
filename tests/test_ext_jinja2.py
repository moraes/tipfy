# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.jinja2
"""
import os
import unittest

from _base import get_app, get_environ, get_request, get_response
from tipfy import local, Response
from tipfy.ext.jinja2 import render_template, render_response


current_dir = os.path.abspath(os.path.dirname(__file__))
templates_dir = os.path.join(current_dir, 'files', 'jinja2')


class TestJinja2(unittest.TestCase):
    def test_render_template(self):
        app = get_app({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})
        message = 'Hello, World!'
        res = render_template('template1.html', message=message)
        assert res == message

    def test_render_response(self):
        app = get_app({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})
        local.response = get_response()
        message = 'Hello, World!'
        response = render_response('template1.html', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/html'
        assert response.data == message
