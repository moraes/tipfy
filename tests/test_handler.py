import unittest

from tipfy import (Request, RequestHandler, Response, Rule, Tipfy,
    ALLOWED_METHODS)


class TestHandler(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_405(self):
        class HomeHandler(RequestHandler):
            pass

        app = Tipfy(rules=[
            Rule('/', endpoint='home', handler=HomeHandler),
        ])

        client = app.get_test_client()

        for method in ALLOWED_METHODS:
            response = client.open('/', method=method)
            self.assertEqual(response.status_code, 405)

    def test_405_debug(self):
        class HomeHandler(RequestHandler):
            pass

        app = Tipfy(rules=[
            Rule('/', endpoint='home', handler=HomeHandler),
        ], debug=True)

        client = app.get_test_client()

        for method in ALLOWED_METHODS:
            response = client.open('/', method=method)
            self.assertEqual(response.status_code, 405)

    def test_abort(self):
        class HandlerWith400(RequestHandler):
            def get(self, **kwargs):
                self.abort(400)

        class HandlerWith403(RequestHandler):
            def post(self, **kwargs):
                self.abort(403)

        class HandlerWith404(RequestHandler):
            def put(self, **kwargs):
                self.abort(404)

        app = Tipfy(rules=[
            Rule('/400', endpoint='400', handler=HandlerWith400),
            Rule('/403', endpoint='403', handler=HandlerWith403),
            Rule('/404', endpoint='404', handler=HandlerWith404),
        ], debug=True)

        client = app.get_test_client()

        response = client.get('/400')
        self.assertEqual(response.status_code, 400)

        response = client.post('/403')
        self.assertEqual(response.status_code, 403)

        response = client.put('/404')
        self.assertEqual(response.status_code, 404)

    def test_get_config(self):
        pass

    def test_handle_exception(self):
        class HandlerWithValueError(RequestHandler):
            def get(self, **kwargs):
                raise ValueError()

        class HandlerWithNotImplementedError(RequestHandler):
            def get(self, **kwargs):
                raise NotImplementedError()

            def handle_exception(self, exception=None, debug=True):
                return Response('I fixed it!')

        app = Tipfy(rules=[
            Rule('/value-error', endpoint='value-error', handler=HandlerWithValueError),
            Rule('/not-implemented-error', endpoint='not-implemented-error', handler=HandlerWithNotImplementedError),
        ], debug=True)

        client = app.get_test_client()

        self.assertRaises(ValueError, client.get, '/value-error')

        response = client.get('/not-implemented-error')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'I fixed it!')

    def test_redirect(self):
        class HomeHandler(RequestHandler):
            def get(self, **kwargs):
                return Response('Home sweet home!')

        class HandlerWithRedirect(RequestHandler):
            def get(self, **kwargs):
                return self.redirect('/')

        app = Tipfy(rules=[
            Rule('/', endpoint='home', handler=HomeHandler),
            Rule('/redirect-me', endpoint='redirect', handler=HandlerWithRedirect),
        ], debug=True)

        client = app.get_test_client()
        response = client.get('/redirect-me', follow_redirects=True)
        self.assertEqual(response.data, 'Home sweet home!')

    def test_redirect_to(self):
        class HomeHandler(RequestHandler):
            def get(self, **kwargs):
                return Response('Home sweet home!')

        class HandlerWithRedirectTo(RequestHandler):
            def get(self, **kwargs):
                return self.redirect_to('home')

        app = Tipfy(rules=[
            Rule('/', endpoint='home', handler=HomeHandler),
            Rule('/redirect-me', endpoint='redirect', handler=HandlerWithRedirectTo),
        ], debug=True)

        client = app.get_test_client()
        response = client.get('/redirect-me', follow_redirects=True)
        self.assertEqual(response.data, 'Home sweet home!')

    def test_redirect_relative_uris(self):
        app = Tipfy()
        class Handler(RequestHandler):
            pass

        request = Request.from_values('/foo/bar/')
        handler = Handler(app, request)
        response = handler.redirect('/baz')
        self.assertEqual(response.headers['Location'], 'http://localhost/baz')

        response = handler.redirect('./baz')
        self.assertEqual(response.headers['Location'], 'http://localhost/foo/bar/baz')

        response = handler.redirect('../baz')
        self.assertEqual(response.headers['Location'], 'http://localhost/foo/baz')

        request = Request.from_values('/foo/bar')
        handler = Handler(app, request)
        response = handler.redirect('/baz')
        self.assertEqual(response.headers['Location'], 'http://localhost/baz')

        response = handler.redirect('./baz')
        self.assertEqual(response.headers['Location'], 'http://localhost/foo/baz')

        response = handler.redirect('../baz')
        self.assertEqual(response.headers['Location'], 'http://localhost/baz')

    def test_url_for(self):
        pass
