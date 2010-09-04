import os
import unittest

from tipfy import (Request, RequestHandler, Response, Rule, Tipfy,
    ALLOWED_METHODS)


class TestApp(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None

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

    def test_dev(self):
        app = Tipfy()
        self.assertEqual(app.dev, False)

        os.environ['SERVER_SOFTWARE'] = 'Dev'
        app = Tipfy()
        self.assertEqual(app.dev, True)
        os.environ.pop('SERVER_SOFTWARE')

    def test_app_id(self):
        app = Tipfy()
        self.assertEqual(app.app_id, None)

        os.environ['APPLICATION_ID'] = 'myapp'
        app = Tipfy()
        self.assertEqual(app.app_id, 'myapp')
        os.environ.pop('APPLICATION_ID')

    def test_version_id(self):
        app = Tipfy()
        self.assertEqual(app.version_id, '1')

        os.environ['CURRENT_VERSION_ID'] = 'testing'
        app = Tipfy()
        self.assertEqual(app.version_id, 'testing')
        os.environ.pop('CURRENT_VERSION_ID')
