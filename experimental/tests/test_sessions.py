import unittest

from gaetestbed import DataStoreTestCase, MemcacheTestCase

from tipfy import Tipfy, Request, RequestHandler, Response, Rule
from tipfy.sessions import (AllSessionMixins, DatastoreSession, SessionStore,
    SecureCookieStore, SecureCookieSession, SessionMiddleware)
from tipfy.sessions.appengine import SessionModel


class BaseHandler(RequestHandler, AllSessionMixins):
    middleware = [SessionMiddleware()]


class TestSessionStore(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def _get_app(self):
        return Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            }
        })

    def test_secure_cookie_store(self):
        app = self._get_app()
        store = SessionStore(app, Request.from_values('/'))

        self.assertEqual(isinstance(store.secure_cookie_store, SecureCookieStore), True)

    def test_secure_cookie_store_no_secret_key(self):
        app = Tipfy()
        store = SessionStore(app, Request.from_values('/'))

        self.assertRaises(KeyError, getattr, store, 'secure_cookie_store')

    def test_get_cookie_args(self):
        app = self._get_app()
        store = SessionStore(app, Request.from_values('/'))

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
        app = self._get_app()
        store = SessionStore(app, Request.from_values('/'))

        session = store.get_session()
        self.assertEqual(isinstance(session, SecureCookieSession), True)
        self.assertEqual(session, {})

        session['foo'] = 'bar'

        response = Response()
        store.save(response)

        app = self._get_app()
        request = Request.from_values('/', headers=[('Cookie', response.headers['Set-Cookie'])])
        store = SessionStore(app, request)

        session = store.get_session()
        self.assertEqual(isinstance(session, SecureCookieSession), True)
        self.assertEqual(session, {'foo': 'bar'})

    def test_set_delete_cookie(self):
        app = self._get_app()
        store = SessionStore(app, Request.from_values('/'))

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

    def test_factory(self):
        app = Tipfy()
        app.set_locals(Request.from_values('/'))
        self.assertEqual(isinstance(SessionStore.factory(app, 'session_store'), SessionStore), True)


class TestSessionMixins(DataStoreTestCase, MemcacheTestCase,
    unittest.TestCase):

    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)

    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def _get_app(self, *args, **kwargs):
        app = Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
        })
        app.set_locals(Request.from_values(*args, **kwargs))
        return app

    def test_session(self):
        class MyHandler(BaseHandler):
            def get(self):
                res = self.session.get('key')
                if not res:
                    res = 'undefined'
                    session = SecureCookieSession()
                    session['key'] = 'a session value'
                    self.set_session(self.session_store.config['cookie_name'], session)

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
                session = self.get_session(backend='memcache')
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
                session = self.get_session(backend='datastore')
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
                    self.set_cookie('test', 'a cookie value')
                else:
                    self.delete_cookie('test')

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
                    self.set_cookie('test', 'a cookie value')

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

                cookie = self.get_secure_cookie('test') or {}
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

    def test_set_get_flash(self):
        class MyHandler(BaseHandler):
            def get(self):
                res = self.get_flash()
                if not res:
                    res = [{'body': 'undefined'}]
                    self.set_flash({'body': 'a flash value'})

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
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_get_by_sid_without_cache(self):
        sid = 'test'
        entity = SessionModel.create(sid, {'foo': 'bar', 'baz': 'ding'})
        entity.put()

        cached_data = SessionModel.get_cache(sid)
        assert cached_data is not None

        entity.delete_cache()
        cached_data = SessionModel.get_cache(sid)
        assert cached_data is None

        entity = SessionModel.get_by_sid(sid)
        assert entity is not None

        # Now will fetch cache.
        entity = SessionModel.get_by_sid(sid)
        assert entity is not None

        assert 'foo' in entity.data
        assert 'baz' in entity.data
        assert entity.data['foo'] == 'bar'
        assert entity.data['baz'] == 'ding'

        entity.delete()
        entity = SessionModel.get_by_sid(sid)
        assert entity is None
