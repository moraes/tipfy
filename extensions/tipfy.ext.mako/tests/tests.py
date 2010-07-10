# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.mako
"""
import os
import sys
import unittest

from mako.lookup import TemplateLookup

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

    def test_engine_factory(self):
        def get_mako_env():
            app = Tipfy.app
            dirs = app.get_config('tipfy.ext.mako', 'templates_dir')
            if isinstance(dirs, basestring):
                dirs = [dirs]

            return TemplateLookup(directories=dirs, output_encoding='utf-8',
                encoding_errors='replace')


        app = Tipfy({'tipfy.ext.mako': {
            'templates_dir': templates_dir,
            'engine_factory': get_mako_env,
        }})

        message = 'Hello, World!'
        res = mako.render_template('template1.html', message=message)
        assert res == message + '\n'

    def test_engine_factory2(self):
        old_sys_path = sys.path[:]
        sys.path.insert(0, current_dir)

        app = Tipfy({'tipfy.ext.mako': {
            'templates_dir': templates_dir,
            'engine_factory': 'resources.get_mako_env',
        }})

        message = 'Hello, World!'
        res = mako.render_template('template1.html', message=message)
        assert res == message + '\n'

        sys.path = old_sys_path
