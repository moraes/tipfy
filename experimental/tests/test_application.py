import os
import unittest

from tipfy import (Request, RequestHandler, Response, Rule, Tipfy,
    ALLOWED_METHODS)
from tipfy.sessions import SessionStore, SecureCookieSession


class BrokenHandler(RequestHandler):
    def get(self, **kwargs):
        raise ValueError('booo!')


class BrokenButFixedHandler(BrokenHandler):
    def handle_exception(self, exception=None, debug=False):
        # Let's fix it.
        return Response('that was close!', status=200)


class Handle404(RequestHandler):
    def handle_exception(self, exception=None, debug=False):
        return Response('404 custom handler', status=404)


class Handle405(RequestHandler):
    def handle_exception(self, exception=None, debug=False):
        response = Response('405 custom handler', status=405)
        response.headers['Allow'] = 'GET'
        return response


class Handle500(RequestHandler):
    def handle_exception(self, exception=None, debug=False):
        return Response('500 custom handler', status=500)


class TestApp(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_200(self):
        class MyHandler(RequestHandler):
            def delete(self, **kwargs):
                return Response('Method: %s' % self.request.method)

            get = head = options = post = put = trace = delete

        app = Tipfy(rules=[Rule('/', name='home', handler=MyHandler)])
        client = app.get_test_client()

        for method in ALLOWED_METHODS:
            response = client.open('/', method=method)
            self.assertEqual(response.status_code, 200, method)
            if method == 'HEAD':
                self.assertEqual(response.data, '')
            else:
                self.assertEqual(response.data, 'Method: %s' % method)

    def test_404(self):
        # No URL rules defined.
        app = Tipfy()
        client = app.get_test_client()
        response = client.get('/')
        self.assertEqual(response.status_code, 404)

    def test_404_debug(self):
        # No URL rules defined.
        app = Tipfy(debug=True)
        client = app.get_test_client()
        response = client.get('/')
        self.assertEqual(response.status_code, 404)

    def test_500(self):
        # Handler import will fail.
        app = Tipfy(rules=[Rule('/', name='home', handler='non.existent.handler')])
        client = app.get_test_client()
        response = client.get('/')
        self.assertEqual(response.status_code, 500)

    def test_500_debug(self):
        # Handler import will fail.
        app = Tipfy(rules=[Rule('/', name='home', handler='non.existent.handler')], debug=True)
        client = app.get_test_client()
        self.assertRaises(ImportError, client.get, '/')

    def test_501(self):
        # Method is not in ALLOWED_METHODS.
        app = Tipfy()
        client = app.get_test_client()
        response = client.open('/', method='CONNECT')
        self.assertEqual(response.status_code, 501)

    def test_501_debug(self):
        # Method is not in ALLOWED_METHODS.
        app = Tipfy(debug=True)
        client = app.get_test_client()
        response = client.open('/', method='CONNECT')
        self.assertEqual(response.status_code, 501)


class TestHandleException(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_custom_error_handlers(self):
        class HomeHandler(RequestHandler):
            def get(self):
                return Response('')

        app = Tipfy([
            Rule('/', handler=HomeHandler, name='home'),
            Rule('/broken', handler=BrokenHandler, name='broken'),
        ], debug=False)
        app.error_handlers = {
            404: Handle404,
            405: Handle405,
            500: Handle500,
        }
        client = app.get_test_client()

        res = client.get('/nowhere')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data, '404 custom handler')

        res = client.put('/')
        self.assertEqual(res.status_code, 405)
        self.assertEqual(res.data, '405 custom handler')
        self.assertEqual(res.headers.get('Allow'), 'GET')

        res = client.get('/broken')
        self.assertEqual(res.status_code, 500)
        self.assertEqual(res.data, '500 custom handler')


class TestRequest(unittest.TestCase):
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

    def test_session_store(self):
        app = self._get_app()
        request = Request.from_values('/')
        app.set_locals(request)
        store = SessionStore(app)

        self.assertEqual(isinstance(request.session_store, SessionStore), True)

    def test_session(self):
        app = self._get_app()
        request = Request.from_values('/')
        app.set_locals(request)
        store = SessionStore(app)

        session = request.session
        self.assertEqual(isinstance(session, SecureCookieSession), True)
        self.assertEqual(session, {})
