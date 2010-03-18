# -*- coding: utf-8 -*-
"""
    Tests for tipfy.RequestHandler.
"""
import unittest

from nose.tools import assert_raises, raises

import tipfy

RESPONSE = 'Hello, World!'

class MyHandler(tipfy.RequestHandler):
    def get(self, **kwargs):
        return RESPONSE


class TestRequestHandler(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()
        MyHandler.middleware = []

    @raises(tipfy.MethodNotAllowed)
    def test_method_not_allowed(self):
        handler = MyHandler()
        handler.dispatch('foo')

    def test_dispatch_without_middleware(self):
        handler = MyHandler()
        assert handler.dispatch('get') == RESPONSE
