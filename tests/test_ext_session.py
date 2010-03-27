# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.session
"""
import unittest
from nose.tools import raises

import _base

import tipfy
from tipfy import get_config, local, local_manager
from tipfy.ext.session import SessionStore, SecureCookie

def get_app(config=None):
    return tipfy.WSGIApplication({
        'tipfy.ext.session': {
            'secret_key': 'foo',
        },
    })


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



class TestSessionStore(unittest.TestCase):
    def setUp(self):
        self.app = get_app()
        self.provider = StoreProvider()

        local.sessions = SessionStore(self.provider)

    def tearDown(self):
        local_manager.cleanup()

        self.app = None
        self.provider = None
        self.store = None

    def test_get_session(self):
        local.request = tipfy.Request.from_values()

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        session = local.sessions.get_session()

        assert isinstance(session, SecureCookie)
        assert session.new is True
        assert 'tipfy.session' in local.sessions._data
        assert 'tipfy.session' in local.sessions._data_args

        # Getting a session for trhe second time will return the same session.
        session_2 = local.sessions.get_session()
        assert session == session_2

    def test_get_session_with_key(self):
        local.request = tipfy.Request.from_values()

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        session = local.sessions.get_session('my_session')

        assert isinstance(session, SecureCookie)
        assert session.new is True
        assert 'my_session' in local.sessions._data
        assert 'my_session' in local.sessions._data_args

    def test_get_session_with_args(self):
        local.request = tipfy.Request.from_values()

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        session = local.sessions.get_session(max_age=86400)

        assert isinstance(session, SecureCookie)
        assert session.new is True
        assert 'tipfy.session' in local.sessions._data
        assert 'tipfy.session' in local.sessions._data_args
        assert local.sessions._data_args['tipfy.session'] == {'max_age': 86400}

    def test_get_existing_session(self):

        cookie = SecureCookie([('foo', 'bar')], secret_key=self.provider.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'tipfy.session=%s' % cookie.serialize(),
        })

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        session = local.sessions.get_session()

        assert isinstance(session, SecureCookie)
        assert session.new is False
        assert session['foo'] == 'bar'

    def test_get_existing_but_invalid_session(self):
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'tipfy.session=bar'
        })

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        session = local.sessions.get_session()

        assert isinstance(session, SecureCookie)
        assert session.new is False
        assert len(session) == 0

    def test_delete_session(self):
        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        local.sessions.delete_session('foo')

        assert local.sessions._data == {'foo': None}
        assert local.sessions._data_args == {'foo': {}}

    def test_delete_session_and_existing_data(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.provider.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_session=%s' % cookie.serialize(),
        })

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        cookie = local.sessions.get_secure_cookie('my_session', max_age=86400)

        assert len(cookie) == 1
        assert cookie['foo'] == 'bar'

        local.sessions.delete_session('my_session')

        assert len(cookie) == 0
        assert 'bar' not in cookie

        assert local.sessions._data == {'my_session': None}
        assert local.sessions._data_args == {'my_session': {}}

    def test_get_secure_cookie(self):
        local.request = tipfy.Request.from_values()

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        cookie = local.sessions.get_secure_cookie('foo', max_age=86400)

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert 'foo' in local.sessions._data
        assert 'foo' in local.sessions._data_args
        assert len(cookie) == 0
        assert local.sessions._data_args['foo'] == {'max_age': 86400}

    def test_get_secure_cookie_existing(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.provider.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_session=%s' % cookie.serialize(),
        })

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        cookie = local.sessions.get_secure_cookie('my_session', max_age=86400)

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is False
        assert len(cookie) == 1
        assert cookie['foo'] == 'bar'

        assert 'my_session' in local.sessions._data
        assert 'my_session' in local.sessions._data_args

        assert local.sessions._data_args['my_session'] == {'max_age': 86400}

    def test_get_secure_cookie_existing_but_invalid(self):
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_session=bar',
        })

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        cookie = local.sessions.get_secure_cookie('my_session', max_age=86400)

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is False
        assert len(cookie) == 0

        assert 'my_session' in local.sessions._data
        assert 'my_session' in local.sessions._data_args

        assert local.sessions._data_args['my_session'] == {'max_age': 86400}

    def test_get_secure_cookie_without_load(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.provider.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_session=%s' % cookie.serialize(),
        })

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        cookie = local.sessions.get_secure_cookie('my_session', load=False, max_age=86400)

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert len(cookie) == 0

        assert 'my_session' in local.sessions._data
        assert 'my_session' in local.sessions._data_args

        assert local.sessions._data_args['my_session'] == {'max_age': 86400}

    def test_load_secure_cookie(self):
        local.request = tipfy.Request.from_values()

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        cookie = local.sessions.load_secure_cookie('foo')

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert len(cookie) == 0

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

    def test_load_secure_cookie_existing(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.provider.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_session=%s' % cookie.serialize(),
        })

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        cookie = local.sessions.load_secure_cookie('my_session')

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is False
        assert len(cookie) == 1
        assert cookie['foo'] == 'bar'

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

    def test_load_secure_cookie_existing_but_invalid(self):
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_session=bar',
        })

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        cookie = local.sessions.load_secure_cookie('my_session')

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is False
        assert len(cookie) == 0

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

    def test_create_secure_cookie(self):
        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        cookie = local.sessions.create_secure_cookie()

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert len(cookie) == 0

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

    def test_create_secure_cookie_with_data(self):
        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        cookie = local.sessions.create_secure_cookie(data={'foo': 'bar'})

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert len(cookie) == 1
        assert cookie['foo'] == 'bar'

        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

    def test_set_cookie(self):
        assert local.sessions._data == {}
        assert local.sessions._data_args == {}

        local.sessions.set_cookie('foo', 'bar', max_age=86400)
        assert local.sessions._data == {'foo': 'bar'}
        assert local.sessions._data_args == {'foo': {'max_age': 86400}}

        local.sessions.set_cookie('baz', 'ding')
        assert local.sessions._data == {'foo': 'bar', 'baz': 'ding'}
        assert local.sessions._data_args == {'foo': {'max_age': 86400}, 'baz': {}}
