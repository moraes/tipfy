# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.mako
"""
__import__('pkg_resources').declare_namespace('tipfy.ext')

import os
import unittest

from tipfy import Response, Tipfy
from tipfy.ext import mako


current_dir = os.path.abspath(os.path.dirname(__file__))
templates_dir = os.path.join(current_dir, 'templates')


class TestMako(unittest.TestCase):
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

    def test_mako_mixin(self):
        class MyHandler(mako.MakoMixin):
            def __init__(self):
                self.context = {}

        app = Tipfy({'tipfy.ext.mako': {'templates_dir': templates_dir}})
        message = 'Hello, World!'

        handler = MyHandler()
        response = handler.render_response('template1.html', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/html'
        assert response.data == message + '\n'
