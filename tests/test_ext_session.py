# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.session
"""
import unittest
from nose.tools import raises
from gaetestbed import DataStoreTestCase, MemcacheTestCase

from google.appengine.api import memcache
from google.appengine.ext import db

import _base

import tipfy
from tipfy import get_config, local, local_manager
from tipfy.ext.session import (DatastoreSession, DatastoreSessionStore,
    MessagesMixin, SecureCookie, Session, SessionMiddleware, SessionMixin,
    SessionStore)

def set_app(config=None):
    return tipfy.WSGIApplication({
        'tipfy.ext.session': {
            'secret_key': 'foo',
        },
    })


class Response(object):
    """A fake response object with cookies."""
    def __init__(self):
        self.cookies_to_set = {}
        self.cookie_args = {}
        self.cookies_to_delete = {}

    def set_cookie(self, key, value, **kwargs):
        self.cookies_to_set[key] = value
        self.cookie_args[key] = kwargs

    def delete_cookie(self, key, **kwargs):
        self.cookies_to_delete[key] = kwargs


class StoreConfig(object):
    def __init__(self):
        module = 'tipfy.ext.session'
        self.session_type =        get_config(module, 'session_type')
        self.secret_key =          get_config(module, 'secret_key')
        self.default_session_key = get_config(module, 'session_cookie_name')
        self.default_flash_key =   get_config(module, 'flash_cookie_name')
        self.default_cookie_args = {
                       'session_expires': get_config(module, 'cookie_session_expires'),
                       'max_age':         get_config(module, 'cookie_max_age'),
                       'domain':          get_config(module, 'cookie_domain'),
                       'path':            get_config(module, 'cookie_path'),
                       'secure':          get_config(module, 'cookie_secure'),
                       'httponly':        get_config(module, 'cookie_httponly'),
                       'force':           get_config(module, 'cookie_force'),
        }


class TestSessionMiddleware(unittest.TestCase):
    def setUp(self):
        set_app()

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
            'session_expires': local.app.config.get('tipfy.ext.session', 'cookie_session_expires'),
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

    def test_pre_dispatch_handler(self):
        middleware = SessionMiddleware()
        middleware.pre_dispatch_handler()

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
        middleware = SessionMiddleware()
        response = Response()

        assert getattr(local, 'session_store', None) is None
        middleware.pre_dispatch(None)
        assert isinstance(local.session_store, SessionStore)

        local.session_store.set_flash({'foo': 'bar'})
        assert 'tipfy.flash' not in response.cookies_to_set
        response = middleware.post_dispatch(None, response)
        assert 'tipfy.flash' in response.cookies_to_set

    def test_post_dispatch_handler(self):
        middleware = SessionMiddleware()
        response = Response()

        assert getattr(local, 'session_store', None) is None
        middleware.pre_dispatch_handler()
        assert isinstance(local.session_store, SessionStore)

        local.session_store.set_flash({'foo': 'bar'})
        assert 'tipfy.flash' not in response.cookies_to_set
        response = middleware.post_dispatch_handler(response)
        assert 'tipfy.flash' in response.cookies_to_set


class TestSessionMixin(unittest.TestCase):
    def setUp(self):
        set_app()
        self.config = StoreConfig()
        local.session_store = SessionStore(self.config)

    def tearDown(self):
        local_manager.cleanup()
        self.config = None

    def test_get_session(self):
        middleware = SessionMiddleware()
        middleware.pre_dispatch(None)
        local.request = tipfy.Request.from_values()

        mixin = SessionMixin()
        assert isinstance(mixin.session, SecureCookie)

    def test_get_flash(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.config.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'tipfy.flash=%s' % cookie.serialize(),
        })

        mixin = SessionMixin()
        flash = mixin.get_flash()
        assert isinstance(flash, SecureCookie)
        assert len(flash) == 1
        assert flash['foo'] == 'bar'

        # The second time should not work.
        flash = mixin.get_flash()
        assert flash is None

    def test_get_flash_custom_key(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.config.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'my_flash=%s' % cookie.serialize(),
        })

        mixin = SessionMixin()
        flash = mixin.get_flash('my_flash')
        assert isinstance(flash, SecureCookie)
        assert len(flash) == 1
        assert flash['foo'] == 'bar'

    def test_get_flash_invalid_flash(self):
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'tipfy.flash=foo',
        })

        mixin = SessionMixin()
        flash = mixin.get_flash()
        assert flash is None

    def test_get_flash_no_flash(self):
        local.request = tipfy.Request.from_values()

        mixin = SessionMixin()
        flash = mixin.get_flash()
        assert flash is None

    def test_set_flash(self):
        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        mixin = SessionMixin()
        flash = mixin.set_flash({'foo': 'bar'})

        assert 'tipfy.flash' in local.session_store._data
        assert local.session_store._data_args == {'tipfy.flash': {}}


class TestMessagesMixin(unittest.TestCase):
    def setUp(self):
        set_app()
        self.config = StoreConfig()
        local.session_store = SessionStore(self.config)
        local.request = tipfy.Request.from_values()

    def tearDown(self):
        local_manager.cleanup()
        self.config = None

    def test_messages_mixin(self):
        mixin = MessagesMixin()
        assert mixin.messages == []

    def test_messages_mixin_with_flash(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.config.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'tipfy.flash=%s' % cookie.serialize(),
        })

        mixin = MessagesMixin()

        assert mixin.messages == [{'foo': 'bar'}]

        mixin.set_message('success', 'Hello, world!', title='HAI', life=5000, flash=False)

        assert mixin.messages == [{'foo': 'bar'}, {'level': 'success', 'title': 'HAI', 'body': 'Hello, world!', 'life': 5000}]

    def test_messages_mixin_set_message(self):
        mixin = MessagesMixin()
        mixin.set_message('success', 'Hello, world!', title='HAI', life=5000, flash=False)

        assert mixin.messages == [{'level': 'success', 'title': 'HAI', 'body': 'Hello, world!', 'life': 5000}]

    def test_messages_mixin_set_message_flash(self):
        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        mixin = MessagesMixin()
        mixin.set_message('success', 'Hello, world!', title='HAI', life=5000, flash=True)

        assert mixin.messages == []
        assert 'tipfy.flash' in local.session_store._data
        assert local.session_store._data_args == {'tipfy.flash': {}}

    def test_messages_mixin_set_form_error(self):
        mixin = MessagesMixin()
        mixin.set_form_error('Hello, world!', title='HAI')

        assert mixin.messages == [{'level': 'error', 'title': 'HAI', 'body': 'Hello, world!', 'life': None}]

    def test_messages_mixin_set_form_error_no_body_no_title(self):
        mixin = MessagesMixin()
        mixin.set_form_error()

        assert mixin.messages == [{'level': 'error', 'title': 'Error', 'body': 'A problem occurred. Please correct the errors listed in the form.', 'life': None}]


class TestSessionStore(unittest.TestCase):
    def setUp(self):
        set_app()
        self.config = StoreConfig()
        local.session_store = SessionStore(self.config)

    def tearDown(self):
        local.session_store = None
        local_manager.cleanup()
        self.config = None

    def test_save_no_session(self):
        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        local.session_store.save(None)

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

    def test_save_delete_flashes(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.config.secret_key)
        local.request = tipfy.Request.from_values(headers={
            'Cookie':   'tipfy.flash=%s; my_flash=%s' % (cookie.serialize(), cookie.serialize()),
        })

        response = Response()

        flash = local.session_store.get_flash()
        flash2 = local.session_store.get_flash('my_flash')

        local.session_store.save(response)

        assert local.session_store._data['tipfy.flash'] is None
        assert local.session_store._data['my_flash'] is None

        assert 'tipfy.flash' in response.cookies_to_delete
        assert 'my_flash' in response.cookies_to_delete

    def test_save_with_max_age(self):
        response = Response()
        local.session_store.set_cookie('foo', 'bar', max_age=86400)
        local.session_store.save(response)

        assert local.session_store._data['foo'] == 'bar'

        assert 'foo' in response.cookies_to_set
        assert 'foo' in response.cookie_args
        assert 'max_age' in response.cookie_args['foo']

    def test_save_with_session_expires(self):
        local.request = tipfy.Request.from_values()
        response = Response()
        cookie = local.session_store.get_secure_cookie('foo', session_expires=86400)
        cookie['foo'] = 'bar'
        local.session_store.save(response)

        assert 'foo' in response.cookies_to_set
        assert 'foo' in response.cookie_args
        assert 'session_expires' in local.session_store._data_args['foo']

    def test_get_session(self):
        local.request = tipfy.Request.from_values()

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        session = local.session_store.get_session()

        assert isinstance(session, SecureCookie)
        assert session.new is True
        assert 'tipfy.session' in local.session_store._data
        assert 'tipfy.session' in local.session_store._data_args

        # Getting a session for the second time will return the same session.
        session_2 = local.session_store.get_session()
        assert session is session_2

    def test_get_session_with_key(self):
        local.request = tipfy.Request.from_values()

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        session = local.session_store.get_session('my_session')

        assert isinstance(session, SecureCookie)
        assert session.new is True
        assert 'my_session' in local.session_store._data
        assert 'my_session' in local.session_store._data_args

        # Getting a session for the second time will return the same session.
        session_2 = local.session_store.get_session('my_session')
        assert session is session_2

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

    def test_get_session_with_max_age(self):
        local.request = tipfy.Request.from_values()

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        session = local.session_store.get_session(max_age=86400)
        session['foo'] = 'bar'

        response = Response()
        local.session_store.save(response)

        assert self.config.default_session_key in response.cookies_to_set
        assert response.cookie_args[self.config.default_session_key]['max_age'] is None
        assert response.cookie_args[self.config.default_session_key]['expires'] is not None

    def test_get_session_after_deletion(self):
        local.request = tipfy.Request.from_values()

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        session = local.session_store.get_session('my_session')

        assert isinstance(session, SecureCookie)
        assert 'my_session' in local.session_store._data
        assert 'my_session' in local.session_store._data_args

        local.session_store.delete_session('my_session')

        # Getting a session for the second time will return the same session.
        session_2 = local.session_store.get_session('my_session')
        assert session is not session_2

    def test_get_existing_session(self):
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.config.secret_key)
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
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.config.secret_key)
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
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.config.secret_key)
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
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.config.secret_key)
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
        cookie = SecureCookie([('foo', 'bar')], secret_key=self.config.secret_key)
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


class TestDatastoreSessionStore(DataStoreTestCase, MemcacheTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)
        set_app()
        self.config = StoreConfig()
        local.session_store = DatastoreSessionStore(self.config)

    def tearDown(self):
        local_manager.cleanup()
        self.config = None

    def test_init(self):
        pass

    def test_sid(self):
        cookie = SecureCookie([('sid', 'bar')], secret_key=self.config.secret_key)
        session = DatastoreSession(cookie)

    def test_get_entity(self):
        pass

    def test_init_with_cookie(self):
        cookie = SecureCookie([('sid', 'bar')], secret_key=self.config.secret_key)
        session = DatastoreSession(cookie)

    def test_delete_entity(self):
        cookie = SecureCookie([('sid', 'bar')], secret_key=self.config.secret_key)
        session = DatastoreSession(cookie)

        session.delete()

    def test_get_session_after_deletion(self):
        local.request = tipfy.Request.from_values()

        assert local.session_store._data == {}
        assert local.session_store._data_args == {}

        session = local.session_store.get_session('my_session')

        assert isinstance(session, DatastoreSession)
        assert 'my_session' in local.session_store._data
        assert 'my_session' in local.session_store._data_args

        local.session_store.delete_session('my_session')

        # Getting a session for the second time will return the same session.
        session_2 = local.session_store.get_session('my_session')
        assert session is not session_2

class TestDatastoreSession(DataStoreTestCase, MemcacheTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)
        set_app()
        self.config = StoreConfig()
        local.session_store = DatastoreSessionStore(self.config)

    def tearDown(self):
        local_manager.cleanup()
        self.config = None

    def test_get_session(self):
        local.request = tipfy.Request.from_values()
        session = local.session_store._load_session('foo')
        assert isinstance(session, DatastoreSession)

    def test_delete_session(self):
        cookie = SecureCookie([('sid', 'bar')], secret_key=self.config.secret_key)
        session = DatastoreSession(cookie)
        session['foo'] = 'bar'

        assert len(session) == 1
        assert session['foo'] == 'bar'

        local.session_store._delete_session(session)

        assert len(session) == 0

    def test_save_cookie(self):
        cookie = SecureCookie([('sid', 'bar')], secret_key=self.config.secret_key)
        session = DatastoreSession(cookie)
        session['foo'] = 'bar'

        response = Response()
        session.save_cookie(response, self.config.default_session_key)

        session_entity = Session.get_by_sid('bar')
        assert isinstance(session_entity, db.Model)
        assert session_entity.data == {'foo': 'bar'}

    def test_delete(self):
        cookie = SecureCookie([('sid', 'foo')], secret_key=self.config.secret_key)
        session = DatastoreSession(cookie)
        session['foo'] = 'bar'

        response = Response()
        session.save_cookie(response, self.config.default_session_key)

        assert Session.get_by_sid('foo') is not None
        assert memcache.get('foo', namespace=Session.get_namespace()) is not None

        session.delete()

        assert Session.get_by_sid('foo') is None
        assert memcache.get('foo', namespace=Session.get_namespace()) is None

class TestSession(DataStoreTestCase, MemcacheTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)
        set_app()
        self.config = StoreConfig()

    def test_get_by_sid(self):
        session = Session(key_name='foo', data={})
        session.put()

        session_entity = Session.get_by_sid('foo')
        assert isinstance(session_entity, db.Model)

        session_entity = Session.get_by_sid('foo')
        assert isinstance(session_entity, db.Model)

        session_in_memcache = memcache.get('foo', namespace=Session.get_namespace())
        assert session_in_memcache is not None

    def test_get_by_sid2(self):
        session = Session(key_name='foo', data={})
        session.put()

        memcache.delete('foo', namespace=Session.get_namespace())

        assert Session.get_by_sid('foo') is not None
        assert memcache.get('foo', namespace=Session.get_namespace()) is not None

    def test_delete(self):
        session = Session(key_name='foo', data={})
        session.put()

        assert Session.get_by_sid('foo') is not None
        assert memcache.get('foo', namespace=Session.get_namespace()) is not None

        session.delete()

        assert Session.get_by_sid('foo') is None
        assert memcache.get('foo', namespace=Session.get_namespace()) is None
