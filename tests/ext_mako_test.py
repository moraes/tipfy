# -*- coding: utf-8 -*-
"""
    Tests for tipfyext.mako
"""
import os
import sys
import unittest

from tipfy import RequestHandler, Request, Response, Tipfy
from tipfy.app import local
from tipfyext.mako import Mako, MakoMixin

import test_utils

current_dir = os.path.abspath(os.path.dirname(__file__))
templates_dir = os.path.join(current_dir, 'resources', 'mako_templates')


class TestMako(test_utils.BaseTestCase):
    def test_render_template(self):
        app = Tipfy(config={'tipfyext.mako': {'templates_dir': templates_dir}})
        request = Request.from_values()
        handler = RequestHandler(app, request)
        mako = Mako(app)

        message = 'Hello, World!'
        res = mako.render_template(handler, 'template1.html', message=message)
        self.assertEqual(res, message + '\n')

    def test_render_response(self):
        app = Tipfy(config={'tipfyext.mako': {'templates_dir': templates_dir}})
        request = Request.from_values()
        handler = RequestHandler(app, request)
        mako = Mako(app)

        message = 'Hello, World!'
        response = mako.render_response(handler, 'template1.html', message=message)
        self.assertEqual(isinstance(response, Response), True)
        self.assertEqual(response.mimetype, 'text/html')
        self.assertEqual(response.data, message + '\n')

    def test_mako_mixin_render_template(self):
        class MyHandler(RequestHandler, MakoMixin):
            def __init__(self, app, request):
                self.app = app
                self.request = request
                self.context = {}

        app = Tipfy(config={'tipfyext.mako': {'templates_dir': templates_dir}})
        request = Request.from_values()
        handler = MyHandler(app, request)
        mako = Mako(app)
        message = 'Hello, World!'

        response = handler.render_template('template1.html', message=message)
        self.assertEqual(response, message + '\n')

    def test_mako_mixin_render_response(self):
        class MyHandler(RequestHandler, MakoMixin):
            def __init__(self, app, request):
                self.app = app
                self.request = request
                self.context = {}

        app = Tipfy(config={'tipfyext.mako': {'templates_dir': templates_dir}})
        request = Request.from_values()
        handler = MyHandler(app, request)
        mako = Mako(app)
        message = 'Hello, World!'

        response = handler.render_response('template1.html', message=message)
        self.assertEqual(isinstance(response, Response), True)
        self.assertEqual(response.mimetype, 'text/html')
        self.assertEqual(response.data, message + '\n')


if __name__ == '__main__':
    test_utils.main()
