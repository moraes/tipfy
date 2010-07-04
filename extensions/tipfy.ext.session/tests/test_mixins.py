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

from tipfy import Request, RequestHandler, Response, Tipfy
from tipfy.ext.session import (AllSessionMixins, SessionStore,
    SessionMiddleware)


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


class BaseHandler(RequestHandler, AllSessionMixins):
    middleware = [SessionMiddleware]


class TestAllSessionMixins(DataStoreTestCase, MemcacheTestCase,
    unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)
        self.app = Tipfy({
            'tipfy.ext.session': {
                'secret_key': 'test',
            },
        })

    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_session(self):
        class MyHandler(BaseHandler):
            def get(self):
                res = self.session.get('test')
                if not res:
                    res = 'undefined'
                    self.session['test'] = 'a session value'

                return Response(res)

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a session value'

    def test_get_session(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.get_session(backend='securecookie')
                res = session.get('test')
                if not res:
                    res = 'undefined'
                    session['test'] = 'a session value'

                return Response(res)

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a session value'

    def test_get_memcache_session(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.get_session(backend='memcache')
                res = session.get('test')
                if not res:
                    res = 'undefined'
                    session['test'] = 'a session value'

                return Response(res)

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a session value'

    def test_get_memcache_session_with_expires(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.get_session(backend='memcache', session_expires=86400)
                res = session.get('test')
                if not res:
                    res = 'undefined'
                    session['test'] = 'a session value'

                return Response(res)

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a session value'

    def test_get_memcache_session_with_max_age(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.get_session(backend='memcache', max_age=86400)
                res = session.get('test')
                if not res:
                    res = 'undefined'
                    session['test'] = 'a session value'

                return Response(res)

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a session value'

    def test_get_datastore_session(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.get_session(backend='datastore')
                res = session.get('test')
                if not res:
                    res = 'undefined'
                    session['test'] = 'a session value'

                return Response(res)

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a session value'

    def test_delete_cookie_session(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.get_session(backend='securecookie')
                res = session.get('test')
                if not res:
                    res = 'undefined'
                    session['test'] = 'a session value'

                self.delete_cookie('tipfy.session')
                return Response(res)

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'undefined'

    def test_delete_memcache_session(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.get_session(backend='memcache')
                res = session.get('test')
                if not res:
                    res = 'undefined'
                    session['test'] = 'a session value'

                self.delete_cookie('tipfy.session')
                return Response(res)

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'undefined'

    def test_delete_datastore_session(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.get_session(backend='datastore')
                res = session.get('test')
                if not res:
                    res = 'undefined'
                    session['test'] = 'a session value'

                self.delete_cookie('tipfy.session')
                return Response(res)

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'undefined'

    def test_delete_datastore_session2(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.get_session(backend='datastore')
                res = session.get('test')
                if not res:
                    res = 'undefined'
                    session['test'] = 'a session value'
                else:
                    self.delete_cookie('tipfy.session')

                return Response(res)

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a session value'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

    @raises(KeyError)
    def test_get_invalid_session_backend(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.get_session(backend='i_dont_exist')
                res = session.get('test')
                if not res:
                    res = 'undefined'
                    session['test'] = 'a session value'

                return Response(res)

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

    def test_get_flash(self):
        class MyHandler(BaseHandler):
            def get(self):
                res = self.get_flash()
                if not res:
                    res = [{'body': 'undefined'}]
                    self.set_flash({'body': 'a flash value'})

                return Response(res[0]['body'])


        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a flash value'

    def test_get_flash_from_memcache(self):
        class MyHandler(BaseHandler):
            def get(self):
                res = self.get_flash(backend='memcache')
                if not res:
                    res = [{'body': 'undefined'}]
                    self.set_flash({'body': 'a flash value'})

                return Response(res[0]['body'])


        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a flash value'

    def test_get_flash_from_datastore(self):
        class MyHandler(BaseHandler):
            def get(self):
                res = self.get_flash(backend='datastore')
                if not res:
                    res = [{'body': 'undefined'}]
                    self.set_flash({'body': 'a flash value'})

                return Response(res[0]['body'])


        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a flash value'

    def test_get_messages(self):
        class MyHandler(BaseHandler):
            def get(self):
                self.set_message('success', 'a normal message value')
                self.set_message('success', 'a flash message value', flash=True)
                return Response('|'.join(msg['body'] for msg in self.messages))


        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'a normal message value'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a flash message value|a normal message value'

    def test_set_cookie(self):
        class MyHandler(BaseHandler):
            def get(self):
                res = self.request.cookies.get('test')
                if not res:
                    res = 'undefined'
                    self.set_cookie('test', 'a cookie value')

                return Response(res)


        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a cookie value'

    def test_delete_cookie(self):
        class MyHandler(BaseHandler):
            def get(self):
                res = self.request.cookies.get('test')
                if not res:
                    res = 'undefined'
                    self.set_cookie('test', 'a cookie value')
                else:
                    self.delete_cookie('test')

                return Response(res)


        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a cookie value'

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

    def test_get_secure_cookie(self):
        class MyHandler(BaseHandler):
            def get(self):
                cookie = self.get_secure_cookie('test')
                res = cookie.get('test')
                if not res:
                    res = 'undefined'
                    cookie['test'] = 'a secure cookie value'

                return Response(res)


        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a secure cookie value'

    def test_get_secure_cookie_always_new(self):
        class MyHandler(BaseHandler):
            def get(self):
                cookie = self.get_secure_cookie('test', load=False)
                res = cookie.get('test')
                if not res:
                    res = 'undefined'
                    cookie['test'] = 'a secure cookie value'

                return Response(res)


        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'undefined'

    def test_create_secure_cookie(self):
        class MyHandler(BaseHandler):
            def get(self):
                cookie = self.get_secure_cookie('new-cookie')
                res = cookie.get('test')
                if not res:
                    res = 'undefined'
                    new_cookie = self.session_store.create_secure_cookie()
                    new_cookie['test'] = 'a new secure cookie value'
                    self.set_cookie('new-cookie', new_cookie)

                return Response(res)


        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})

        assert response.data == 'undefined'

        handler = MyHandler(self.app, get_request(self.app, headers={
            'Cookie': response.headers.getlist('Set-Cookie'),
        }))
        response = handler.dispatch('get', **{})
        assert response.data == 'a new secure cookie value'

    @raises(ValueError)
    def test_create_secure_cookie_invalid_value(self):
        class MyHandler(BaseHandler):
            def get(self):
                self.session_store.create_secure_cookie('foo')
                return Response(res)

        handler = MyHandler(self.app, get_request(self.app))
        response = handler.dispatch('get', **{})
