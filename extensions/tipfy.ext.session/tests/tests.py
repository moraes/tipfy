# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.session datastore backend
"""
from datetime import datetime, timedelta
import unittest

from nose.tools import raises
from gaetestbed import DataStoreTestCase, MemcacheTestCase

from google.appengine.api import memcache
from google.appengine.ext import db

from werkzeug.contrib.securecookie import SecureCookie

from tipfy import Request, Response, Tipfy
from tipfy.ext.session import (SessionStore, SessionMiddleware)


def get_request(app, *args, **kwargs):
    request = Request.from_values(*args, **kwargs)
    app.set_request(request)
    return request


def get_config(app):
    config = app.get_config('tipfy.ext.session').copy()
    config['cookie_args'] = {
        'session_expires': config.get('cookie_session_expires'),
        'max_age':         config.get('cookie_max_age'),
        'domain':          config.get('cookie_domain'),
        'path':            config.get('cookie_path'),
        'secure':          config.get('cookie_secure'),
        'httponly':        config.get('cookie_httponly'),
        'force':           config.get('cookie_force'),
    }
    return config


class TestSessionStore(DataStoreTestCase, MemcacheTestCase,
    unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)
        self.app = Tipfy({
            'tipfy.ext.session': {
                'secret_key': 'test',
            },
        })

    def test_get_flash(self):
        config = get_config(self.app)
        cookie = SecureCookie({'_flash': [('foo', 'bar')]},
            secret_key=config['secret_key'])

        request = get_request(self.app, headers={
            'Cookie': 'tipfy.session=%s' % cookie.serialize(),
        })

        backends = SessionMiddleware.default_backends
        store = SessionStore(request, config, backends, 'securecookie')

        flash = store.get_flash()
        assert isinstance(flash, list)
        assert len(flash) == 1
        assert flash[0] == ('foo', 'bar')

        # The second time should not work.
        flash = store.get_flash()
        assert flash == []

    def test_set_flash(self):
        config = get_config(self.app)
        request = get_request(self.app)
        backends = SessionMiddleware.default_backends
        store = SessionStore(request, config, backends, 'securecookie')

        store.set_flash(('foo', 'bar'))

        cookie = SecureCookie({'_flash': [('foo', 'bar')]},
            secret_key=config['secret_key'])

        response = Response()
        store.save_session(response)

        assert response.headers['Set-Cookie'] == 'tipfy.session="%s"; Path=/' % cookie.serialize()

    def test_save_session_empty(self):
        config = get_config(self.app)
        request = get_request(self.app)
        backends = SessionMiddleware.default_backends
        store = SessionStore(request, config, backends, 'securecookie')

        response = Response()
        store.save_session(response)

        assert 'Set-Cookie' not in response.headers

    def test_save_session_delete_cookie(self):
        config = get_config(self.app)
        request = get_request(self.app)
        backends = SessionMiddleware.default_backends
        store = SessionStore(request, config, backends, 'securecookie')

        store.delete_cookie('foo', path='/baz')
        store.delete_cookie('foo2')

        response = Response()
        store.save_session(response)

        assert response.headers.getlist('Set-Cookie') == [
            'foo=; expires=Thu, 01-Jan-1970 00:00:00 GMT; Max-Age=0; Path=/baz',
            'foo2=; expires=Thu, 01-Jan-1970 00:00:00 GMT; Max-Age=0; Path=/'
        ]

    def test_save_session_set_cookie(self):
        config = get_config(self.app)
        request = get_request(self.app)
        backends = SessionMiddleware.default_backends
        store = SessionStore(request, config, backends, 'securecookie')

        store.set_cookie('foo', 'bar', path='/baz')
        store.set_cookie('foo2', 'bar2')

        response = Response()
        store.save_session(response)

        assert response.headers.getlist('Set-Cookie') == [
            'foo=bar; Path=/baz',
            'foo2=bar2; Path=/'
        ]

    def test_set_cookie(self):
        config = get_config(self.app)
        request = get_request(self.app)
        backends = SessionMiddleware.default_backends
        store = SessionStore(request, config, backends, 'securecookie')

        store.set_cookie('foo', 'bar', path='/baz')
        store.set_cookie('foo2', 'bar2')

        assert store._data['foo'] == ('bar', {'path': '/baz'})
        assert store._data['foo2'] == ('bar2', {})

    def test_delete_cookie(self):
        config = get_config(self.app)
        request = get_request(self.app)
        backends = SessionMiddleware.default_backends
        store = SessionStore(request, config, backends, 'securecookie')

        store.delete_cookie('foo', path='/baz')
        store.delete_cookie('foo2')

        assert store._data['foo'] == (None, {'path': '/baz'})
        assert store._data['foo2'] == (None, {})

    def test_create_secure_cookie(self):
        config = get_config(self.app)
        request = get_request(self.app)
        backends = SessionMiddleware.default_backends
        store = SessionStore(request, config, backends, 'securecookie')

        cookie = store.create_secure_cookie()

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert len(cookie) == 0

    def test_create_secure_cookie_with_data(self):
        config = get_config(self.app)
        request = get_request(self.app)
        backends = SessionMiddleware.default_backends
        store = SessionStore(request, config, backends, 'securecookie')

        cookie = store.create_secure_cookie(data={'foo': 'bar'})

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert len(cookie) == 1
        assert cookie['foo'] == 'bar'

    @raises(ValueError)
    def test_create_secure_cookie_with_none_data(self):
        config = get_config(self.app)
        request = get_request(self.app)
        backends = SessionMiddleware.default_backends
        store = SessionStore(request, config, backends, 'securecookie')

        cookie = store.create_secure_cookie('foo')

    def test_get_secure_cookie_without_load(self):
        config = get_config(self.app)
        cookie = SecureCookie([('foo', 'bar')], secret_key=config['secret_key'])
        request = get_request(self.app, headers={
            'Cookie': 'my_session=%s' % cookie.serialize(),
        })
        backends = SessionMiddleware.default_backends
        store = SessionStore(request, config, backends, 'securecookie')

        cookie = store.get_secure_cookie('my_session', load=False, max_age=86400)

        assert isinstance(cookie, SecureCookie)
        assert cookie.new is True
        assert len(cookie) == 0

        assert 'my_session' in store._data
        assert store._data['my_session'][1] == {'max_age': 86400}
