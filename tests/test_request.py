import os
import sys
import unittest

from tipfy import Request, RequestHandler, Response, Rule, Tipfy
from tipfy.app import local
from tipfy.sessions import SessionStore, SecureCookieSession
from tipfy.auth.appengine import AppEngineAuthStore
from tipfy.utils import json_decode, json_encode


class TestRequest(unittest.TestCase):
    def tearDown(self):
        local.__release_local__()

    def _get_app(self):
        return Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            }
        })

    def test_request_json(self):
        class HomeHandler(RequestHandler):
            def get(self, **kwargs):
                return Response(self.request.json['foo'])

        app = Tipfy(rules=[
            Rule('/', name='home', handler=HomeHandler),
        ], debug=True)

        data = json_encode({'foo': 'bar'})
        client = app.get_test_client()
        response = client.get('/', content_type='application/json', data=data)
        self.assertEqual(response.data, 'bar')

    def test_session_store(self):
        app = self._get_app()
        request = Request.from_values('/')
        local.current_handler = handler = RequestHandler(app, request)

        self.assertEqual(isinstance(handler.session_store, SessionStore), True)

    def test_session(self):
        app = self._get_app()
        request = Request.from_values('/')
        local.current_handler = handler = RequestHandler(app, request)

        session = handler.session
        self.assertEqual(isinstance(session, SecureCookieSession), True)
        self.assertEqual(session, {})

    def test_auth_store(self):
        app = self._get_app()
        request = Request.from_values('/')
        local.current_handler = handler = RequestHandler(app, request)

        self.assertEqual(isinstance(handler.auth, AppEngineAuthStore), True)

