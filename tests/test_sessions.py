import os
import unittest

from gaetestbed import DataStoreTestCase, MemcacheTestCase

from werkzeug import cached_property

from tipfy import Tipfy, Request, RequestHandler, Response, Rule
from tipfy.app import local
from tipfy.sessions import (SecureCookieSession, SecureCookieStore,
    SessionMiddleware, SessionStore)
from tipfy.appengine.sessions import (DatastoreSession, MemcacheSession,
    SessionModel)


class BaseHandler(RequestHandler):
    middleware = [SessionMiddleware()]


class TestSessionStoreBase(unittest.TestCase):
    def tearDown(self):
        local.__release_local__()

    def _get_app(self):
        return Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            }
        })

    def test_secure_cookie_store(self):
        local.current_handler = handler = RequestHandler(self._get_app(), Request.from_values())
        store = SessionStore(handler)

        self.assertEqual(isinstance(store.secure_cookie_store, SecureCookieStore), True)

    def test_secure_cookie_store_no_secret_key(self):
        local.current_handler = handler = RequestHandler(Tipfy(), Request.from_values())
        store = SessionStore(handler)

        self.assertRaises(KeyError, getattr, store, 'secure_cookie_store')

    def test_get_cookie_args(self):
        local.current_handler = handler = RequestHandler(self._get_app(), Request.from_values())
        store = SessionStore(handler)

        self.assertEqual(store.get_cookie_args(), {
            'max_age':     None,
            'domain':      None,
            'path':        '/',
            'secure':      None,
            'httponly':    False,
        })

        self.assertEqual(store.get_cookie_args(max_age=86400, domain='.foo.com'), {
            'max_age':     86400,
            'domain':      '.foo.com',
            'path':        '/',
            'secure':      None,
            'httponly':    False,
        })

    def test_get_save_session(self):
        local.current_handler = handler = RequestHandler(self._get_app(), Request.from_values())
        store = SessionStore(handler)

        session = store.get_session()
        self.assertEqual(isinstance(session, SecureCookieSession), True)
        self.assertEqual(session, {})

        session['foo'] = 'bar'

        response = Response()
        store.save(response)

        request = Request.from_values('/', headers={'Cookie': '\n'.join(response.headers.getlist('Set-Cookie'))})
        local.current_handler = handler = RequestHandler(self._get_app(), request)
        store = SessionStore(handler)

        session = store.get_session()
        self.assertEqual(isinstance(session, SecureCookieSession), True)
        self.assertEqual(session, {'foo': 'bar'})

    def test_set_delete_cookie(self):
        local.current_handler = handler = RequestHandler(self._get_app(), Request.from_values())
        store = SessionStore(handler)

        store.set_cookie('foo', 'bar')
        store.set_cookie('baz', 'ding')

        response = Response()
        store.save(response)

        headers = {'Cookie': '\n'.join(response.headers.getlist('Set-Cookie'))}
        request = Request.from_values('/', headers=headers)

        self.assertEqual(request.cookies.get('foo'), 'bar')
        self.assertEqual(request.cookies.get('baz'), 'ding')

        store.delete_cookie('foo')
        store.save(response)

        headers = {'Cookie': '\n'.join(response.headers.getlist('Set-Cookie'))}
        request = Request.from_values('/', headers=headers)

        self.assertEqual(request.cookies.get('foo', None), '')
        self.assertEqual(request.cookies['baz'], 'ding')


class TestSessionStore(DataStoreTestCase, MemcacheTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)

        SessionStore.default_backends.update({
            'datastore':    DatastoreSession,
            'memcache':     MemcacheSession,
            'securecookie': SecureCookieSession,
        })

    def tearDown(self):
        local.__release_local__()

    def _get_app(self, *args, **kwargs):
        app = Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
        })
        local.current_handler = handler = RequestHandler(app, Request.from_values(*args, **kwargs))
        return app

    def test_set_session(self):
        class MyHandler(BaseHandler):
            def get(self):
                res = self.session.get('key')
                if not res:
                    res = 'undefined'
                    session = SecureCookieSession()
                    session['key'] = 'a session value'
                    self.session_store.set_session(self.session_store.config['cookie_name'], session)

                return Response(res)

        rules = [Rule('/', name='test', handler=MyHandler)]

        app = self._get_app('/')
        app.router.add(rules)
        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'undefined')

        response = client.get('/', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'a session value')

    def test_set_session_datastore(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.session_store.get_session(backend='datastore')
                res = session.get('key')
                if not res:
                    res = 'undefined'
                    session = DatastoreSession(None, 'a_random_session_id')
                    session['key'] = 'a session value'
                    self.session_store.set_session(self.session_store.config['cookie_name'], session, backend='datastore')

                return Response(res)

        rules = [Rule('/', name='test', handler=MyHandler)]

        app = self._get_app('/')
        app.router.add(rules)
        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'undefined')

        response = client.get('/', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'a session value')

    def test_get_memcache_session(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.session_store.get_session(backend='memcache')
                res = session.get('test')
                if not res:
                    res = 'undefined'
                    session['test'] = 'a memcache session value'

                return Response(res)

        rules = [Rule('/', name='test', handler=MyHandler)]

        app = self._get_app('/')
        app.router.add(rules)
        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'undefined')

        response = client.get('/', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'a memcache session value')

    def test_get_datastore_session(self):
        class MyHandler(BaseHandler):
            def get(self):
                session = self.session_store.get_session(backend='datastore')
                res = session.get('test')
                if not res:
                    res = 'undefined'
                    session['test'] = 'a datastore session value'

                return Response(res)

        rules = [Rule('/', name='test', handler=MyHandler)]

        app = self._get_app('/')
        app.router.add(rules)
        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'undefined')

        response = client.get('/', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'a datastore session value')

    def test_set_delete_cookie(self):
        class MyHandler(BaseHandler):
            def get(self):
                res = self.request.cookies.get('test')
                if not res:
                    res = 'undefined'
                    self.session_store.set_cookie('test', 'a cookie value')
                else:
                    self.session_store.delete_cookie('test')

                return Response(res)

        rules = [Rule('/', name='test', handler=MyHandler)]

        app = self._get_app('/')
        app.router.add(rules)
        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'undefined')

        response = client.get('/', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'a cookie value')

        response = client.get('/', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'undefined')

        response = client.get('/', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'a cookie value')

    def test_set_unset_cookie(self):
        class MyHandler(BaseHandler):
            def get(self):
                res = self.request.cookies.get('test')
                if not res:
                    res = 'undefined'
                    self.session_store.set_cookie('test', 'a cookie value')

                self.session_store.unset_cookie('test')
                return Response(res)

        rules = [Rule('/', name='test', handler=MyHandler)]

        app = self._get_app('/')
        app.router.add(rules)
        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'undefined')

        response = client.get('/', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'undefined')

    def test_set_get_secure_cookie(self):
        class MyHandler(BaseHandler):
            def get(self):
                response = Response()

                cookie = self.session_store.get_secure_cookie('test') or {}
                res = cookie.get('test')
                if not res:
                    res = 'undefined'
                    self.session_store.set_secure_cookie(response, 'test', {'test': 'a secure cookie value'})

                response.data = res
                return response

        rules = [Rule('/', name='test', handler=MyHandler)]

        app = self._get_app('/')
        app.router.add(rules)
        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'undefined')

        response = client.get('/', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'a secure cookie value')

    def test_set_get_flashes(self):
        class MyHandler(BaseHandler):
            def get(self):
                res = [msg for msg, level in self.session.get_flashes()]
                if not res:
                    res = [{'body': 'undefined'}]
                    self.session.flash({'body': 'a flash value'})

                return Response(res[0]['body'])

        rules = [Rule('/', name='test', handler=MyHandler)]

        app = self._get_app('/')
        app.router.add(rules)
        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'undefined')

        response = client.get('/', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'a flash value')

    def test_set_get_messages(self):
        class MyHandler(BaseHandler):
            @cached_property
            def messages(self):
                """A list of status messages to be displayed to the user."""
                messages = []
                flashes = self.session.get_flashes(key='_messages')
                for msg, level in flashes:
                    msg['level'] = level
                    messages.append(msg)

                return messages

            def set_message(self, level, body, title=None, life=None, flash=False):
                """Adds a status message.

                :param level:
                    Message level. Common values are "success", "error", "info" or
                    "alert".
                :param body:
                    Message contents.
                :param title:
                    Optional message title.
                :param life:
                    Message life time in seconds. User interface can implement
                    a mechanism to make the message disappear after the elapsed time.
                    If not set, the message is permanent.
                :returns:
                    None.
                """
                message = {'title': title, 'body': body, 'life': life}
                if flash is True:
                    self.session.flash(message, level, '_messages')
                else:
                    self.messages.append(message)

            def get(self):
                self.set_message('success', 'a normal message value')
                self.set_message('success', 'a flash message value', flash=True)
                return Response('|'.join(msg['body'] for msg in self.messages))

        rules = [Rule('/', name='test', handler=MyHandler)]

        app = self._get_app('/')
        app.router.add(rules)
        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'a normal message value')

        response = client.get('/', headers={
            'Cookie': '\n'.join(response.headers.getlist('Set-Cookie')),
        })
        self.assertEqual(response.data, 'a flash message value|a normal message value')


class TestSessionModel(DataStoreTestCase, MemcacheTestCase,
    unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)
        self.app = Tipfy()

    def tearDown(self):
        local.__release_local__()

    def test_get_by_sid_without_cache(self):
        sid = 'test'
        entity = SessionModel.create(sid, {'foo': 'bar', 'baz': 'ding'})
        entity.put()

        cached_data = SessionModel.get_cache(sid)
        self.assertNotEqual(cached_data, None)

        entity.delete_cache()
        cached_data = SessionModel.get_cache(sid)
        self.assertEqual(cached_data, None)

        entity = SessionModel.get_by_sid(sid)
        self.assertNotEqual(entity, None)

        # Now will fetch cache.
        entity = SessionModel.get_by_sid(sid)
        self.assertNotEqual(entity, None)

        self.assertEqual('foo' in entity.data, True)
        self.assertEqual('baz' in entity.data, True)
        self.assertEqual(entity.data['foo'], 'bar')
        self.assertEqual(entity.data['baz'], 'ding')

        entity.delete()
        entity = SessionModel.get_by_sid(sid)
        self.assertEqual(entity, None)
