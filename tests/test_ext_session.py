# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.session
"""
import unittest
from nose.tools import raises

from _base import get_environ

import tipfy
from tipfy import local, local_manager
from tipfy.ext import session

def get_app(config=None):
    return tipfy.WSGIApplication({
        'tipfy.ext.session': {
            'secret_key': 'foo',
        },
    })

class Request(object):
    """A fake request object with cookies."""
    def __init__(self, cookies=None):
        self.cookies = cookies or {}


class Response(object):
    """A fake response object with cookies."""
    def __init__(self):
        self.cookies_to_set = []
        self.cookies_to_delete = []

    def set_cookie(self, key, value, **kwargs):
        self.cookies_to_set.append((key, value))

    def delete_cookie(self, key, **kwargs):
        self.cookies_to_delete.append(key)


class TestSessionMiddleware(unittest.TestCase):
    def tearDown(self):
        local_manager.cleanup()

    def test_session_type(self):
        app = get_app()
        middleware = session.SessionMiddleware()
        assert middleware.session_type == app.config.get('tipfy.ext.session', 'session_type')

    def test_secret_key(self):
        app = get_app()
        middleware = session.SessionMiddleware()
        assert middleware.secret_key == app.config.get('tipfy.ext.session', 'secret_key')

    def test_default_session_key(self):
        app = get_app()
        middleware = session.SessionMiddleware()
        assert middleware.default_session_key == app.config.get('tipfy.ext.session', 'session_cookie_name')

    def test_default_flash_key(self):
        app = get_app()
        middleware = session.SessionMiddleware()
        assert middleware.default_flash_key == app.config.get('tipfy.ext.session', 'flash_cookie_name')

    def test_default_flash_key(self):
        app = get_app()
        middleware = session.SessionMiddleware()
        assert middleware.default_cookie_args == {
            'max_age':  app.config.get('tipfy.ext.session', 'cookie_max_age'),
            'domain':   app.config.get('tipfy.ext.session', 'cookie_domain'),
            'path':     app.config.get('tipfy.ext.session', 'cookie_path'),
            'secure':   app.config.get('tipfy.ext.session', 'cookie_secure'),
            'httponly': app.config.get('tipfy.ext.session', 'cookie_httponly'),
        }

    def test_pre_dispatch(self):
        app = get_app()

        assert getattr(local, 'session_store', None) is None

        middleware = session.SessionMiddleware()
        middleware.pre_dispatch(None)

        assert isinstance(local.session_store, session.SessionStore)

    def test_pre_dispatch_datastore(self):
        app = tipfy.WSGIApplication({
            'tipfy.ext.session': {
                'secret_key': 'foo',
                'session_type': 'datastore',
            },
        })

        assert getattr(local, 'session_store', None) is None

        middleware = session.SessionMiddleware()
        middleware.pre_dispatch(None)

        assert isinstance(local.session_store, session.DatastoreSessionStore)

    def test_post_dispatch(self):
        app = get_app()

        assert getattr(local, 'session_store', None) is None

        middleware = session.SessionMiddleware()
        middleware.pre_dispatch(None)

        assert isinstance(local.session_store, session.SessionStore)

        local.session_store.set_flash({'foo': 'bar'})

        response = Response()

        assert 'tipfy.flash' not in response.cookies_to_set
        middleware.post_dispatch(None, response)
        assert 'tipfy.flash' in dict(response.cookies_to_set)



class TestSessionMixin(unittest.TestCase):
    def tearDown(self):
        local_manager.cleanup()

    def test_get_session(self):
        app = get_app()
        assert getattr(local, 'session_store', None) is None
        middleware = session.SessionMiddleware()
        middleware.pre_dispatch(None)
        local.request = tipfy.Request(get_environ())

        mixin = session.SessionMixin()
        assert isinstance(mixin.session, session.SecureCookie)


class TestMessagesMixin(unittest.TestCase):
    def tearDown(self):
        local_manager.cleanup()

    def test_messages_mixin(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request()
        middleware = session.SessionMiddleware()
        middleware.pre_dispatch(None)

        mixin = session.MessagesMixin()
        assert mixin.messages == []

    def test_messages_mixin_set_message(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request()
        middleware = session.SessionMiddleware()
        middleware.pre_dispatch(None)

        mixin = session.MessagesMixin()
        mixin.set_message('success', 'Hello, world!', title='HAI', life=5000, flash=False)

        assert mixin.messages == [{'level': 'success', 'title': 'HAI', 'body': 'Hello, world!', 'life': 5000}]

    def test_messages_mixin_set_form_error(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request()
        middleware = session.SessionMiddleware()
        middleware.pre_dispatch(None)

        mixin = session.MessagesMixin()
        mixin.set_form_error('Hello, world!', title='HAI')

        assert mixin.messages == [{'level': 'error', 'title': 'HAI', 'body': 'Hello, world!', 'life': None}]

class TestSessionStore(unittest.TestCase):
    def tearDown(self):
        local_manager.cleanup()


class TestDatastoreSessionStore(unittest.TestCase):
    def tearDown(self):
        local_manager.cleanup()


class TestDatastoreSession(unittest.TestCase):
    def tearDown(self):
        local_manager.cleanup()
