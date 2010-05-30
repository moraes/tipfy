# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.debugger
"""
import unittest

from nose.tools import raises

import jinja2

from tipfy import local, NotFound, Tipfy
from tipfy.ext.debugger import DebuggerMiddleware
from tipfy.ext.debugger.app import (get_template, render_template, seek,
    readline)

class TestDebuggerMiddleware(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None
        local.__release_local__()

    def test_post_make_app_no_dev(self):
        app = Tipfy({
            'tipfy': {
                'dev': False,
                'middleware': ['tipfy.ext.debugger.DebuggerMiddleware'],
            }
        })

        middleware = DebuggerMiddleware()
        new_app = middleware.post_make_app(app)

        self.assertEqual(new_app.__class__.__name__, 'Tipfy')

    def test_post_make_app_dev(self):
        app = Tipfy({
            'tipfy': {
                'dev': True,
                'middleware': ['tipfy.ext.debugger.DebuggerMiddleware'],
            }
        })

        middleware = DebuggerMiddleware()
        new_app = middleware.post_make_app(app)

        self.assertEqual(new_app.wsgi_app.__class__.__name__, 'DebuggedApplication')

    def test_get_template(self):
        assert isinstance(get_template('source.html'), jinja2.Template)

    def test_render_template(self):
        self.assertEqual(render_template('source.html', lines=[]), '<table class="source">\n\n</table>')

    def test_seek(self):
        """Not much to test here."""
        class NothingHere():
            seek = seek

        assert NothingHere().seek(None) is None

    def test_readline(self):
        """Not much to test here."""
        class NothingHere():
            readline = readline

        nothing = NothingHere()
        nothing._buffer = []
        assert nothing.readline() == ''

    def test_readline2(self):
        """Not much to test here."""
        class NothingHere():
            readline = readline

        nothing = NothingHere()
        nothing._buffer = ['foo']
        assert nothing.readline() == 'foo'


