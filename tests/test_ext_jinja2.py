# -*- coding: utf-8 -*-
"""
    Tests for tipfyext.jinja2
"""
import os
import sys
import unittest

from jinja2 import FileSystemLoader, Environment

from tipfy import RequestHandler, Request, Response, Tipfy
from tipfyext.jinja2 import Jinja2, Jinja2Mixin

current_dir = os.path.abspath(os.path.dirname(__file__))
templates_dir = os.path.join(current_dir, 'resources', 'templates')
templates_compiled_target = os.path.join(current_dir, 'resources', 'templates_compiled')


class TestJinja2(unittest.TestCase):
    def tearDown(self):
        Tipfy.app.clear_locals()

    def test_render_template(self):
        app = Tipfy(config={'tipfyext.jinja2': {'templates_dir': templates_dir}})
        app.set_locals(Request.from_values())
        jinja2 = Jinja2(app)

        message = 'Hello, World!'
        res = jinja2.render_template('template1.html', message=message)
        self.assertEqual(res, message)

    def test_render_template_with_i18n(self):
        app = Tipfy(config={
            'tipfyext.jinja2': {
                'templates_dir': templates_dir,
                'environment_args': dict(
                    autoescape=True,
                    extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_', 'jinja2.ext.i18n'],
                ),
            },
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
        })
        app.set_locals(Request.from_values())
        jinja2 = Jinja2(app)

        message = 'Hello, i18n World!'
        res = jinja2.render_template('template2.html', message=message)
        self.assertEqual(res, message)

    def test_render_response(self):
        app = Tipfy(config={'tipfyext.jinja2': {'templates_dir': templates_dir}})
        app.set_locals(Request.from_values())
        jinja2 = Jinja2(app)

        message = 'Hello, World!'
        response = jinja2.render_response('template1.html', message=message)
        self.assertEqual(isinstance(response, Response), True)
        self.assertEqual(response.mimetype, 'text/html')
        self.assertEqual(response.data, message)

    def test_render_response_force_compiled(self):
        app = Tipfy(config={
            'tipfyext.jinja2': {
                'templates_compiled_target': templates_compiled_target,
                'force_use_compiled': True,
            }
        }, debug=False)
        app.set_locals(Request.from_values())
        jinja2 = Jinja2(app)

        message = 'Hello, World!'
        response = jinja2.render_response('template1.html', message=message)
        self.assertEqual(isinstance(response, Response), True)
        self.assertEqual(response.mimetype, 'text/html')
        self.assertEqual(response.data, message)

    def test_jinja2_mixin_render_template(self):
        class MyHandler(RequestHandler, Jinja2Mixin):
            def __init__(self, app, request):
                self.app = app
                self.request = request
                self.context = {}

        app = Tipfy(config={'tipfyext.jinja2': {'templates_dir': templates_dir}})
        app.set_locals(Request.from_values())
        jinja2 = Jinja2(app)
        message = 'Hello, World!'

        handler = MyHandler(Tipfy.app, Tipfy.request)
        response = handler.render_template('template1.html', message=message)
        self.assertEqual(response, message)

    def test_jinja2_mixin_render_response(self):
        class MyHandler(RequestHandler, Jinja2Mixin):
            def __init__(self, app, request):
                self.app = app
                self.request = request
                self.context = {}

        app = Tipfy(config={'tipfyext.jinja2': {'templates_dir': templates_dir}})
        app.set_locals(Request.from_values())
        jinja2 = Jinja2(app)
        message = 'Hello, World!'

        handler = MyHandler(Tipfy.app, Tipfy.request)
        response = handler.render_response('template1.html', message=message)
        self.assertEqual(isinstance(response, Response), True)
        self.assertEqual(response.mimetype, 'text/html')
        self.assertEqual(response.data, message)

    def test_get_template_attribute(self):
        app = Tipfy(config={'tipfyext.jinja2': {'templates_dir': templates_dir}})
        app.set_locals(Request.from_values())
        jinja2 = Jinja2(app)

        hello = jinja2.get_template_attribute('hello.html', 'hello')
        self.assertEqual(hello('World'), 'Hello, World!')

    def test_engine_factory(self):
        def get_jinja2_env():
            app = Tipfy.app
            cfg = app.get_config('tipfyext.jinja2')

            loader = FileSystemLoader(cfg.get( 'templates_dir'))

            return Environment(loader=loader)

        app = Tipfy(config={'tipfyext.jinja2': {
            'templates_dir': templates_dir,
            'engine_factory': get_jinja2_env,
        }})
        app.set_locals(Request.from_values())
        jinja2 = Jinja2(app)

        message = 'Hello, World!'
        res = jinja2.render_template('template1.html', message=message)
        self.assertEqual(res, message)

    def test_engine_factory2(self):
        old_sys_path = sys.path[:]
        sys.path.insert(0, current_dir)

        app = Tipfy(config={'tipfyext.jinja2': {
            'templates_dir': templates_dir,
            'engine_factory': 'resources.get_jinja2_env',
        }})
        app.set_locals(Request.from_values())
        jinja2 = Jinja2(app)

        message = 'Hello, World!'
        res = jinja2.render_template('template1.html', message=message)
        self.assertEqual(res, message)

        sys.path = old_sys_path

    def test_engine_factory3(self):
        app = Tipfy()
        app.set_locals(Request.from_values())
        _globals = {'message': 'Hey there!'}
        filters = {'ho': lambda e: e + ' Ho!'}
        jinja2 = Jinja2(app, _globals=_globals, filters=filters)

        template = jinja2.environment.from_string("""{{ message|ho }}""")

        self.assertEqual(template.render(), 'Hey there! Ho!')
