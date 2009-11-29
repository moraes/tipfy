# -*- coding: utf-8 -*-
"""
    Tests for tipfy.EventHandler and tipfy.EventManager.
"""
import unittest
import sys
from _base import get_app, get_environ, get_request, get_response


from tipfy.ext.session import set_datastore_session, set_securecookie_session


class TestSession(unittest.TestCase):
    def test_set_datastore_session(self):
        app = get_app()
        self.assertEqual(app.hooks.get('pre_dispatch_handler', None), None)
        self.assertEqual(app.hooks.get('pre_send_response', None), None)

        set_datastore_session(app)

        self.assertEqual(app.hooks.get('pre_dispatch_handler', None) is not None, True)
        self.assertEqual(app.hooks.get('pre_send_response', None) is not None, True)

    def test_set_securecookie_session(self):
        app = get_app()
        self.assertEqual(app.hooks.get('pre_dispatch_handler', None), None)
        self.assertEqual(app.hooks.get('pre_send_response', None), None)

        set_securecookie_session(app)

        self.assertEqual(app.hooks.get('pre_dispatch_handler', None) is not None, True)
        self.assertEqual(app.hooks.get('pre_send_response', None) is not None, True)

    def test_SecureCookieSessionMiddleware(self):
        # Initialize app so that get_config() is available.
        app = get_app()

    def test_SecureCookieSessionMiddleware(self):
        # Initialize app so that get_config() is available.
        app = get_app()


