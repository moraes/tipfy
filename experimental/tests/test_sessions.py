import unittest

from tipfy import Tipfy, Request, Response
from tipfy.sessions import SessionStore, SecureCookieStore, SecureCookieSession


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
