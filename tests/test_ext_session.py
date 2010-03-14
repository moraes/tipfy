# -*- coding: utf-8 -*-
"""
    Tests for tipfy.EventHandler and tipfy.EventManager.
"""
import unittest

from nose.tools import assert_raises, raises

import tipfy
from tipfy.ext.session import get_secure_cookie, set_secure_cookie


class TestSession(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_get_secure_cookie(self):
        pass

    def test_get_secure_cookie_with_key(self):
        pass

    def test_get_secure_cookie_with_data(self):
        pass

    def test_get_secure_cookie_with_key_and_data(self):
        pass

    def test_set_secure_cookie(self):
        pass

    def test_set_secure_cookie_with_cookie(self):
        pass

    def test_set_secure_cookie_with_data(self):
        pass

    def test_set_secure_cookie_with_cookie_and_data(self):
        pass

    """
    def test_set_datastore_session(self):
        app = get_app({'tipfy': {'extensions': []}})
        assert app.hooks.get('pre_dispatch_handler', None) is None, app.hooks.get('pre_dispatch_handler', None)
        assert app.hooks.get('post_dispatch_handler', None) is None

        app = get_app({
            'tipfy': {
                'extensions': ['tipfy.ext.session.datastore'],
            },
            'tipfy.ext.session': {
                'secret_key': 'test',
            }
        })

        assert app.hooks.get('pre_dispatch_handler', None) is not None
        assert app.hooks.get('post_dispatch_handler', None) is not None

    def test_set_securecookie_session(self):
        app = get_app({'tipfy': {'extensions': []}})
        assert app.hooks.get('pre_dispatch_handler', None) is None, app.hooks.get('pre_dispatch_handler', None)
        assert app.hooks.get('post_dispatch_handler', None) is None

        app = get_app({
            'tipfy': {
              'extensions': ['tipfy.ext.session.securecookie'],
            },
            'tipfy.ext.session': {
                'secret_key': 'test',
            }
        })

        assert app.hooks.get('pre_dispatch_handler', None) is not None
        assert app.hooks.get('post_dispatch_handler', None) is not None

    def test_SecureCookieSessionMiddleware(self):
        # Initialize app so that get_config() is available.
        app = get_app()

    def test_SecureCookieSessionMiddleware(self):
        # Initialize app so that get_config() is available.
        app = get_app()
    """
