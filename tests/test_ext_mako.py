# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.mako
"""
import os
import unittest
from _base import get_app, get_environ, get_request, get_response


from tipfy import local, Response
from tipfy.ext.mako import get_lookup, render_template, render_response, \
    TemplateLookup


current_dir = os.path.abspath(os.path.dirname(__file__))
templates_dir = os.path.join(current_dir, 'files', 'mako')


class TestMako(unittest.TestCase):
    def test_get_lookup(self):
        app = get_app({'tipfy.ext.mako': {'templates_dir': templates_dir}})
        assert isinstance(get_lookup(), TemplateLookup)

    def test_render_template(self):
        app = get_app({'tipfy.ext.mako': {'templates_dir': templates_dir}})
        message = 'Hello, World!'
        res = render_template('template1.html', message=message)
        assert res == message + '\n'

    def test_render_response(self):
        local.response = get_response()
        message = 'Hello, World!'
        response = render_response('template1.html', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/html'
        assert response.data == message + '\n'
