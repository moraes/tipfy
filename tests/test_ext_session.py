# -*- coding: utf-8 -*-
"""
    Tests for tipfy.EventHandler and tipfy.EventManager.
"""
import unittest

from _base import get_app, get_environ, get_request, get_response


from tipfy.ext.session import get_secure_cookie, set_secure_cookie


class TestSession(unittest.TestCase):
    def test_set_datastore_session(self):
        app = get_app({'tipfy': {'extensions': []}})
        assert app.hooks.get('pre_dispatch_handler', None) is None, app.hooks.get('pre_dispatch_handler', None)
        assert app.hooks.get('pre_send_response', None) is None

        app = get_app({
            'tipfy': {
                'extensions': ['tipfy.ext.session.datastore'],
            },
            'tipfy.ext.session': {
                'secret_key': 'test',
            }
        })

        assert app.hooks.get('pre_dispatch_handler', None) is not None
        assert app.hooks.get('pre_send_response', None) is not None

    def test_set_securecookie_session(self):
        app = get_app({'tipfy': {'extensions': []}})
        assert app.hooks.get('pre_dispatch_handler', None) is None, app.hooks.get('pre_dispatch_handler', None)
        assert app.hooks.get('pre_send_response', None) is None

        app = get_app({
            'tipfy': {
              'extensions': ['tipfy.ext.session.securecookie'],
            },
            'tipfy.ext.session': {
                'secret_key': 'test',
            }
        })

        assert app.hooks.get('pre_dispatch_handler', None) is not None
        assert app.hooks.get('pre_send_response', None) is not None

    def test_SecureCookieSessionMiddleware(self):
        # Initialize app so that get_config() is available.
        app = get_app()

    def test_SecureCookieSessionMiddleware(self):
        # Initialize app so that get_config() is available.
        app = get_app()
