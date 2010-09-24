import os
import unittest

from tipfy import (Request, RequestHandler, Response, Rule, Tipfy,
    ALLOWED_METHODS)
from tipfy.auth.appengine import AppEngineAuthStore
from tipfy.auth.model import User


class LoginHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('login')


class LogoutHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('logout')


class SignupHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('signup')


app = Tipfy(rules=[
    Rule('/', name='home', handler=None),
    Rule('/login', name='auth/login', handler=LoginHandler),
    Rule('/logout', name='auth/logout', handler=LogoutHandler),
    Rule('/signup', name='auth/signup', handler=SignupHandler),
])
client = app.get_test_client()


class TestAppEngineAuthStorer(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_user_model(self):
        request = Request.from_values('/')
        app.set_locals(request)

        store = AppEngineAuthStore(app, request)
        self.assertEqual(store.user_model, User)

    def test_login_url(self):
        request = Request.from_values('/')
        app.set_locals(request)
        app.router.match(request)

        store = AppEngineAuthStore(app, request)
        self.assertEqual(store.login_url(), app.url_for('auth/login', redirect='/'))

        dev = app.dev
        app.dev = False
        store.config['secure_urls'] = True

        self.assertEqual(store.login_url(), app.url_for('auth/login', redirect='/', _scheme='https'))

        app.dev = dev
        store.config['secure_urls'] = False

    def test_logout_url(self):
        request = Request.from_values('/')
        app.set_locals(request)
        app.router.match(request)

        store = AppEngineAuthStore(app, request)
        self.assertEqual(store.logout_url(), app.url_for('auth/logout', redirect='/'))

    def test_signup_url(self):
        request = Request.from_values('/')
        app.set_locals(request)
        app.router.match(request)

        store = AppEngineAuthStore(app, request)
        self.assertEqual(store.signup_url(), app.url_for('auth/signup', redirect='/'))
