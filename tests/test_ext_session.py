# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.session
"""
import unittest
from nose.tools import raises

import _base

import tipfy
from tipfy import get_config, local, local_manager
from tipfy.ext.session import (DatastoreSessionStore, MessagesMixin,
    SecureCookie, SessionMiddleware, SessionMixin, SessionStore)

def get_app(config=None):
    return tipfy.WSGIApplication({
        'tipfy.ext.session': {
            'secret_key': 'foo',
        },
    })


class Response(object):
    """A fake response object with cookies."""
    def __init__(self):
        self.cookies_to_set = []
        self.cookies_to_delete = []

    def set_cookie(self, key, value, **kwargs):
        self.cookies_to_set.append((key, value))

    def delete_cookie(self, key, **kwargs):
        self.cookies_to_delete.append(key)


class StoreProvider(object):
    def __init__(self):
        module = 'tipfy.ext.session'
        self.session_type =        get_config(module, 'session_type')
        self.secret_key =          get_config(module, 'secret_key')
        self.default_session_key = get_config(module, 'session_cookie_name')
        self.default_flash_key =   get_config(module, 'flash_cookie_name')
        self.default_cookie_args = {
                       'max_age':  get_config(module, 'cookie_max_age'),
                       'domain':   get_config(module, 'cookie_domain'),
                       'path':     get_config(module, 'cookie_path'),
                       'secure':   get_config(module, 'cookie_secure'),
                       'httponly': get_config(module, 'cookie_httponly'),
                       'force':    get_config(module, 'cookie_force'),
        }


class TestSessionMiddleware(unittest.TestCase):
    def setUp(self):
        get_app()

    def tearDown(self):
        local_manager.cleanup()

    def test_session_type(self):
        middleware = SessionMiddleware()
        assert middleware.session_type == local.app.config.get('tipfy.ext.session', 'session_type')

    def test_secret_key(self):
        middleware = SessionMiddleware()
        assert middleware.secret_key == local.app.config.get('tipfy.ext.session', 'secret_key')

    def test_default_session_key(self):
        middleware = SessionMiddleware()
        assert middleware.default_session_key == local.app.config.get('tipfy.ext.session', 'session_cookie_name')

    def test_default_flash_key(self):
        middleware = SessionMiddleware()
        assert middleware.default_flash_key == local.app.config.get('tipfy.ext.session', 'flash_cookie_name')

    def test_default_flash_key(self):
        middleware = SessionMiddleware()
        assert middleware.default_cookie_args == {
            'max_age':  local.app.config.get('tipfy.ext.session', 'cookie_max_age'),
            'domain':   local.app.config.get('tipfy.ext.session', 'cookie_domain'),
            'path':     local.app.config.get('tipfy.ext.session', 'cookie_path'),
            'secure':   local.app.config.get('tipfy.ext.session', 'cookie_secure'),
            'httponly': local.app.config.get('tipfy.ext.session', 'cookie_httponly'),
            'force':    local.app.config.get('tipfy.ext.session', 'cookie_force'),
        }

    def test_pre_dispatch(self):
        assert getattr(local, 'session_store', None) is None

        middleware = SessionMiddleware()
        middleware.pre_dispatch(None)

        assert isinstance(local.session_store, SessionStore)

    def test_pre_dispatch_datastore(self):
        app = tipfy.WSGIApplication({
            'tipfy.ext.session': {
                'secret_key': 'foo',
                'session_type': 'datastore',
            },
        })

        assert getattr(local, 'session_store', None) is None

        middleware = SessionMiddleware()
        middleware.pre_dispatch(None)

        assert isinstance(local.session_store, DatastoreSessionStore)

    def test_post_dispatch(self):
        assert getattr(local, 'session_store', None) is None

        middleware = SessionMiddleware()
        middleware.pre_dispatch(None)

        assert isinstance(local.session_store, SessionStore)

        local.session_store.set_flash({'foo': 'bar'})

        response = Response()

        assert 'tipfy.flash' not in response.cookies_to_set
        middleware.post_dispatch(None, response)
        assert 'tipfy.flash' in dict(response.cookies_to_set)


class TestSessionMixin(unittest.TestCase):
    def setUp(self):
        get_app()

    def tearDown(self):
        local_manager.cleanup()

    def test_get_session(self):
        assert getattr(local, 'session_store', None) is None

        middleware = SessionMiddleware()

        middleware.pre_dispatch(None)
        local.request = tipfy.Request.from_values()

        mixin = SessionMixin()
        assert isinstance(mixin.session, SecureCookie)


class TestMessagesMixin(unittest.TestCase):
    def setUp(self):
        get_app()
        local.request = tipfy.Request.from_values()

    def tearDown(self):
        local_manager.cleanup()

    def test_messages_mixin(self):
        middleware = SessionMiddleware()
        middleware.pre_dispatch(None)

        mixin = MessagesMixin()
        assert mixin.messages == []

    def test_messages_mixin_set_message(self):
        middleware = SessionMiddleware()
        middleware.pre_dispatch(None)

        mixin = MessagesMixin()
        mixin.set_message('success', 'Hello, world!', title='HAI', life=5000, flash=False)

        assert mixin.messages == [{'level': 'success', 'title': 'HAI', 'body': 'Hello, world!', 'life': 5000}]

    def test_messages_mixin_set_form_error(self):
        middleware = SessionMiddleware()
        middleware.pre_dispatch(None)

        mixin = MessagesMixin()
        mixin.set_form_error('Hello, world!', title='HAI')

        assert mixin.messages == [{'level': 'error', 'title': 'HAI', 'body': 'Hello, world!', 'life': None}]


class TestSessionStore(unittest.TestCase):
    def setUp(self):
        self.app = get_app()
        self.provider = StoreProvider()

        local.session_store = SessionStore(self.provider)

    def tearDown(self):
        local_manager.cleanup()

        self.app = None
        self.provider = None

    def test_get_session(self):
        local.request = tipfy.Request.from_values()

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        session = local.session_store.get_session()

        assert isinstance(session, SecureCookie)
        assert session.new is True
        assert 'tipfy.session' in local.session_store._data
        assert 'tipfy.session' in local.session_store._data_args

        # Getting a session for trhe second time will return the same session.
        session_2 = local.session_store.get_session()
        assert session == session_2

    def test_get_session_with_key(self):
        local.request = tipfy.Request.from_values()

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        session = local.session_store.get_session('my_session')

        assert isinstance(session, SecureCookie)
        assert session.new is True
        assert 'my_session' in local.session_store._data
        assert 'my_session' in local.session_store._data_args

    def test_get_session_with_args(self):
        local.request = tipfy.Request.from_values()

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        session = local.session_store.get_session(max_age=86400)

        assert isinstance(session, SecureCookie)
        assert session.new is True
        assert 'tipfy.session' in local.session_store._data
        assert 'tipfy.session' in local.session_store._data_args
        assert local.session_store._data_args['tipfy.session'] == {'max_age': 86400}

    def test_get_existing_session(self):

        cookie = SecureCookie([('foo', 'bar')], secret_key=self.provider.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'tipfy.session=%s' % cookie.serialize(),
        })

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        session = local.session_store.get_session()

        assert isinstance(session, SecureCookie)
        assert session.new is False
        assert session['foo'] == 'bar'

    def test_get_existing_but_invalid_session(self):
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'tipfy.session=bar'
        })

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        session = local.session_store.get_session()

        assert isinstance(session, SecureCookie)
        assert session.new is False
        assert len(session) == 0

    def test_delete_session(self):
        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        local.session_store.delete_session('foo')

        assert local.session_store._data == {'foo': None}
        assert local.session_store._data_args == {'foo': {}}

    def test_delete_session_and_existing_data(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.provider.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_session=%s' % cookie.serialize(),
        })

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        cookie = local.session_store.get_secure_cookie('my_session', max_age=86400)

        assert len(cookie) == 1
        assert cookie['foo'] == 'bar'

        local.session_store.delete_session('my_session')

        assert len(cookie) == 0
        assert 'bar' not in cookie

        assert local.session_store._data == {'my_session': None}
        assert local.session_store._data_args == {'my_session': {}}

    def test_get_secure_cookie(self):
        local.request = tipfy.Request.from_values()

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        cookie = local.session_store.get_secure_cookie('foo', max_age=86400)

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert 'foo' in local.session_store._data
        assert 'foo' in local.session_store._data_args
        assert len(cookie) == 0
        assert local.session_store._data_args['foo'] == {'max_age': 86400}

    def test_get_secure_cookie_existing(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.provider.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_session=%s' % cookie.serialize(),
        })

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        cookie = local.session_store.get_secure_cookie('my_session', max_age=86400)

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is False
        assert len(cookie) == 1
        assert cookie['foo'] == 'bar'

        assert 'my_session' in local.session_store._data
        assert 'my_session' in local.session_store._data_args

        assert local.session_store._data_args['my_session'] == {'max_age': 86400}

    def test_get_secure_cookie_existing_but_invalid(self):
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_session=bar',
        })

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        cookie = local.session_store.get_secure_cookie('my_session', max_age=86400)

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is False
        assert len(cookie) == 0

        assert 'my_session' in local.session_store._data
        assert 'my_session' in local.session_store._data_args

        assert local.session_store._data_args['my_session'] == {'max_age': 86400}

    def test_get_secure_cookie_without_load(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.provider.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_session=%s' % cookie.serialize(),
        })

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        cookie = local.session_store.get_secure_cookie('my_session', load=False, max_age=86400)

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert len(cookie) == 0

        assert 'my_session' in local.session_store._data
        assert 'my_session' in local.session_store._data_args

        assert local.session_store._data_args['my_session'] == {'max_age': 86400}

    def test_load_secure_cookie(self):
        local.request = tipfy.Request.from_values()

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        cookie = local.session_store.load_secure_cookie('foo')

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert len(cookie) == 0

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

    def test_load_secure_cookie_existing(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.provider.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_session=%s' % cookie.serialize(),
        })

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        cookie = local.session_store.load_secure_cookie('my_session')

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is False
        assert len(cookie) == 1
        assert cookie['foo'] == 'bar'

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

    def test_load_secure_cookie_existing_but_invalid(self):
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_session=bar',
        })

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        cookie = local.session_store.load_secure_cookie('my_session')

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is False
        assert len(cookie) == 0

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

    def test_create_secure_cookie(self):
        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        cookie = local.session_store.create_secure_cookie()

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert len(cookie) == 0

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

    def test_create_secure_cookie_with_data(self):
        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        cookie = local.session_store.create_secure_cookie(data={'foo': 'bar'})

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert len(cookie) == 1
        assert cookie['foo'] == 'bar'

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

    def test_set_cookie(self):
        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        local.session_store.set_cookie('foo', 'bar', max_age=86400)
        assert local.session_store._data == {'foo': 'bar'}
        assert local.session_store._data_args == {'foo': {'max_age': 86400}}

        local.session_store.set_cookie('baz', 'ding')
        assert local.session_store._data == {'foo': 'bar', 'baz': 'ding'}
        assert local.session_store._data_args == {'foo': {'max_age': 86400}, 'baz': {}}


class TestDatastoreSessionStore(unittest.TestCase):
    def tearDown(self):
        local_manager.cleanup()


class TestDatastoreSession(unittest.TestCase):
    def tearDown(self):
        local_manager.cleanup()
