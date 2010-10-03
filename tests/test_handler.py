import os
import unittest

from tipfy import Request, RequestHandler, Response, Rule, Tipfy
from tipfy.app import ALLOWED_METHODS

from tipfy.sessions import SecureCookieSession
from tipfy.i18n import I18nStore
from tipfy.auth.appengine import AppEngineAuthStore


class TestHandler(unittest.TestCase):
    def test_405(self):
        class HomeHandler(RequestHandler):
            pass

        app = Tipfy(rules=[
            Rule('/', name='home', handler=HomeHandler),
        ])

        client = app.get_test_client()

        for method in ALLOWED_METHODS:
            response = client.open('/', method=method)
            self.assertEqual(response.status_code, 405)

    def test_405_debug(self):
        class HomeHandler(RequestHandler):
            pass

        app = Tipfy(rules=[
            Rule('/', name='home', handler=HomeHandler),
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
            Rule('/400', name='400', handler=HandlerWith400),
            Rule('/403', name='403', handler=HandlerWith403),
            Rule('/404', name='404', handler=HandlerWith404),
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
            Rule('/value-error', name='value-error', handler=HandlerWithValueError),
            Rule('/not-implemented-error', name='not-implemented-error', handler=HandlerWithNotImplementedError),
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
            Rule('/', name='home', handler=HomeHandler),
            Rule('/redirect-me', name='redirect', handler=HandlerWithRedirect),
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
            Rule('/', name='home', handler=HomeHandler),
            Rule('/redirect-me', name='redirect', handler=HandlerWithRedirectTo),
        ], debug=True)

        client = app.get_test_client()
        response = client.get('/redirect-me', follow_redirects=True)
        self.assertEqual(response.data, 'Home sweet home!')

    def test_redirect_relative_uris(self):
        class MyHandler(RequestHandler):
            def get(self):
                return self.redirect(self.request.args.get('redirect'))

        app = Tipfy(rules=[
            Rule('/foo/bar', name='test1', handler=MyHandler),
            Rule('/foo/bar/', name='test2', handler=MyHandler),
        ])
        client = app.get_test_client()

        response = client.get('/foo/bar/', query_string={'redirect': '/baz'})
        self.assertEqual(response.headers['Location'], 'http://localhost/baz')

        response = client.get('/foo/bar/', query_string={'redirect': './baz'})
        self.assertEqual(response.headers['Location'], 'http://localhost/foo/bar/baz')

        response = client.get('/foo/bar/', query_string={'redirect': '../baz'})
        self.assertEqual(response.headers['Location'], 'http://localhost/foo/baz')

        response = client.get('/foo/bar', query_string={'redirect': '/baz'})
        self.assertEqual(response.headers['Location'], 'http://localhost/baz')

        response = client.get('/foo/bar', query_string={'redirect': './baz'})
        self.assertEqual(response.headers['Location'], 'http://localhost/foo/baz')

        response = client.get('/foo/bar', query_string={'redirect': '../baz'})
        self.assertEqual(response.headers['Location'], 'http://localhost/baz')

    def test_url_for(self):
        class Handler(RequestHandler):
            pass

        app = Tipfy(rules=[
            Rule('/', name='home', handler='handlers.Home'),
            Rule('/about', name='about', handler='handlers.About'),
            Rule('/contact', name='contact', handler='handlers.Contact'),
        ])
        request = Request.from_values('/')
        app.router.match(request)

        handler = Handler(app, request)

        self.assertEqual(handler.url_for('home'), '/')
        self.assertEqual(handler.url_for('about'), '/about')
        self.assertEqual(handler.url_for('contact'), '/contact')

        # Extras
        self.assertEqual(handler.url_for('about', _anchor='history'), '/about#history')
        self.assertEqual(handler.url_for('about', _scheme='https'), 'https://localhost/about')

    def test_attributes(self):
        class Handler(RequestHandler):
            pass

        app = Tipfy(config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
        })
        request = Request.from_values('/')

        handler = Handler(app, request)
        self.assertEqual(isinstance(handler.session, SecureCookieSession), True)
        self.assertEqual(isinstance(handler.auth, AppEngineAuthStore), True)
        self.assertEqual(isinstance(handler.i18n, I18nStore), True)

class TestHandlerMiddleware(unittest.TestCase):
    def test_before_dispatch(self):
        res = 'Intercepted!'
        class MyMiddleware(object):
            def before_dispatch(self, handler):
                return Response(res)

        class MyHandler(RequestHandler):
            middleware = [MyMiddleware()]

            def get(self, **kwargs):
                return Response('default')

        app = Tipfy(rules=[
            Rule('/', name='home', handler=MyHandler),
        ])
        client = app.get_test_client()
        response = client.get('/')
        self.assertEqual(response.data, res)

    def test_after_dispatch(self):
        res = 'Intercepted!'
        class MyMiddleware(object):
            def after_dispatch(self, handler, response):
                response.data += res
                return response

        class MyHandler(RequestHandler):
            middleware = [MyMiddleware()]

            def get(self, **kwargs):
                return Response('default')

        app = Tipfy(rules=[
            Rule('/', name='home', handler=MyHandler),
        ])
        client = app.get_test_client()
        response = client.get('/')
        self.assertEqual(response.data, 'default' + res)

    def test_handle_exception(self):
        res = 'Catched!'
        class MyMiddleware(object):
            def handle_exception(self, handler, exception):
                return Response(res)

        class MyHandler(RequestHandler):
            middleware = [MyMiddleware()]

            def get(self, **kwargs):
                raise ValueError()

        app = Tipfy(rules=[
            Rule('/', name='home', handler=MyHandler),
        ])
        client = app.get_test_client()
        response = client.get('/')
        self.assertEqual(response.data, res)

    def test_handle_exception2(self):
        res = 'I fixed it!'
        class MyMiddleware(object):
            def handle_exception(self, handler, exception):
                raise ValueError()

        class MyHandler(RequestHandler):
            middleware = [MyMiddleware()]

            def get(self, **kwargs):
                raise ValueError()

        class ErrorHandler(RequestHandler):
            def handle_exception(self, exception):
                return Response(res)

        app = Tipfy(rules=[
            Rule('/', name='home', handler=MyHandler),
        ], debug=False)
        app.error_handlers[500] = ErrorHandler

        client = app.get_test_client()
        response = client.get('/')
        self.assertEqual(response.data, res)

    def test_handle_exception2(self):
        class MyMiddleware(object):
            def handle_exception(self, handler, exception):
                raise ValueError()

        class MyHandler(RequestHandler):
            middleware = [MyMiddleware()]

            def get(self, **kwargs):
                raise ValueError()

        class ErrorHandler(RequestHandler):
            def handle_exception(self, exception):
                raise ValueError()

        app = Tipfy(rules=[
            Rule('/', name='home', handler=MyHandler),
        ], debug=False)
        app.error_handlers[500] = ErrorHandler

        client = app.get_test_client()
        response = client.get('/')
        self.assertEqual(response.status_code, 500)

    def test_handle_exception3(self):
        res = 'Catched!'
        class MyMiddleware(object):
            def handle_exception(self, handler, exception):
                pass

        class MyHandler(RequestHandler):
            middleware = [MyMiddleware()]

            def get(self, **kwargs):
                raise ValueError()

        app = Tipfy(rules=[
            Rule('/', name='home', handler=MyHandler),
        ])
        client = app.get_test_client()
        response = client.get('/')
        self.assertEqual(response.status_code, 500)
