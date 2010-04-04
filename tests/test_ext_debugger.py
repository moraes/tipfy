# -*- coding: utf-8 -*-
"""
    Tests for tipfy.application
"""
import unittest

from nose.tools import raises

import _base

import jinja2

import tipfy
from tipfy import local, NotFound, WSGIApplication
from tipfy.ext.debugger import DebuggerMiddleware
from tipfy.ext.debugger.app import get_template, render_template

class TestDebuggerMiddleware(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_pre_run_app_no_dev(self):
        app = WSGIApplication({
            'tipfy': {
                'dev': False,
                'middleware': ['tipfy.ext.debugger.DebuggerMiddleware'],
            }
        })

        middleware = DebuggerMiddleware()
        new_app = middleware.pre_run_app(app)

        self.assertEqual(new_app.__class__.__name__, 'WSGIApplication')

    def test_pre_run_app_dev(self):
        app = WSGIApplication({
            'tipfy': {
                'dev': True,
                'middleware': ['tipfy.ext.debugger.DebuggerMiddleware'],
            }
        })

        middleware = DebuggerMiddleware()
        new_app = middleware.pre_run_app(app)

        self.assertEqual(new_app.__class__.__name__, 'DebuggedApplication')

    def test_get_template(self):
        assert isinstance(get_template('source.html'), jinja2.Template)

    def test_render_template(self):
        self.assertEqual(render_template('source.html', lines=[]), '<table class="source">\n\n</table>')
