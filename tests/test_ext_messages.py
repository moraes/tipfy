# -*- coding: utf-8 -*-
"""
    Tests for tipfy.EventHandler and tipfy.EventManager.
"""
import unittest
import sys
from _base import get_app, get_environ, get_request, get_response


from tipfy import local
from tipfy.ext.messages import set_messages, Messages


def get_app_environ_request(**kwargs):
    app = get_app()
    environ = get_environ(**kwargs)
    request = get_request(environ)
    return app, environ, request


class TestMessages(unittest.TestCase):
    def test_set_messages(self):
        app, environ, request = get_app_environ_request()
        local.request = request

        set_messages(request, app)
        self.assertEqual(isinstance(local.messages, Messages), True)
