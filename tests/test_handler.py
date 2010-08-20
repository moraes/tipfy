import unittest

from tipfy import RequestHandler, Response, Rule, Tipfy

from werkzeug.exceptions import (BadRequest, MethodNotAllowed, NotFound,
    Forbidden)


class TestHandler(unittest.TestCase):
    def test_405(self):
        class HomeHandler(RequestHandler):
            def get(self, **kwargs):
                return Response('Home sweet home!')

            def post(self, **kwargs):
                return Response('Home sweet home!')

        app = Tipfy(rules=[
            Rule('/', endpoint='home', handler=HomeHandler),
        ], debug=True)

        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'Home sweet home!')

        response = client.post('/')
        self.assertEqual(response.data, 'Home sweet home!')

        self.assertRaises(MethodNotAllowed, client.delete, '/')
        self.assertRaises(MethodNotAllowed, client.head, '/')
        self.assertRaises(MethodNotAllowed, client.put, '/')
        self.assertRaises(MethodNotAllowed, client.open, '/', method='OPTIONS')
        self.assertRaises(MethodNotAllowed, client.open, '/', method='TRACE')

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

        self.assertRaises(BadRequest, client.get, '/400')
        self.assertRaises(Forbidden, client.post, '/403')
        self.assertRaises(NotFound, client.put, '/404')

    def test_get_config(self):
        pass

    def test_handle_exception(self):
        class HandlerWithValueError(RequestHandler):
            def get(self, **kwargs):
                try:
                    raise ValueError()
                except Exception, e:
                    self.handle_exception(exception=e, debug=True)

        class HandlerWithNotImplementedError(RequestHandler):
            def get(self, **kwargs):
                try:
                    raise NotImplementedError()
                except Exception, e:
                    self.handle_exception(exception=e, debug=True)

        app = Tipfy(rules=[
            Rule('/value-error', endpoint='value-error', handler=HandlerWithValueError),
            Rule('/not-implemented-error', endpoint='not-implemented-error', handler=HandlerWithNotImplementedError),
        ], debug=True)

        client = app.get_test_client()

        self.assertRaises(ValueError, client.get, '/value-error')
        self.assertRaises(NotImplementedError, client.get, '/not-implemented-error')

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

    def test_url_for(self):
        pass
