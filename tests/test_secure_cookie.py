import time
import unittest

from tipfy import Tipfy, Request, Response
from tipfy.sessions import SessionStore, SecureCookieStore, SecureCookieSession


class TestSecureCookie(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def _get_app(self):
        return Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'something very secret',
            }
        })

    def test_get_cookie_no_cookie(self):
        store = SecureCookieStore('secret')
        request = Request.from_values('/')
        self.assertEqual(store.get_cookie(request, 'session'), None)

    def test_get_cookie_invalid_parts(self):
        store = SecureCookieStore('secret')
        request = Request.from_values('/', headers=[('Cookie', 'session="invalid"; Path=/')])
        self.assertEqual(store.get_cookie(request, 'session'), None)

    def test_get_cookie_invalid_signature(self):
        store = SecureCookieStore('secret')
        request = Request.from_values('/', headers=[('Cookie', 'session="foo|bar|baz"; Path=/')])
        self.assertEqual(store.get_cookie(request, 'session'), None)

    def test_get_cookie_expired(self):
        store = SecureCookieStore('secret')
        request = Request.from_values('/', headers=[('Cookie', 'session="eyJmb28iOiJiYXIifQ==|1284849476|847b472f2fabbf1efef55748a394b6f182acd8be"; Path=/')])
        self.assertEqual(store.get_cookie(request, 'session', max_age=-86400), None)

    def test_get_cookie_badly_encoded(self):
        store = SecureCookieStore('secret')
        timestamp = str(int(time.time()))
        value = 'foo'
        signature = store._get_signature('session', value, timestamp)
        cookie_value = '|'.join([value, timestamp, signature])

        request = Request.from_values('/', headers=[('Cookie', 'session="%s"; Path=/' % cookie_value)])
        self.assertEqual(store.get_cookie(request, 'session'), None)

    def test_get_cookie_valid(self):
        store = SecureCookieStore('secret')
        request = Request.from_values('/', headers=[('Cookie', 'session="eyJmb28iOiJiYXIifQ==|1284849476|847b472f2fabbf1efef55748a394b6f182acd8be"; Path=/')])
        self.assertEqual(store.get_cookie(request, 'session'), {'foo': 'bar'})
