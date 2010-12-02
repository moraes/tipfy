# -*- coding: utf-8 -*-
"""
    Tests for tipfy.app
"""
from __future__ import with_statement

import os
import sys
import unittest

from . import BaseTestCase

from tipfy import Request, RequestHandler, Response, Rule, Tipfy
from tipfy.utils import json_encode


class AllMethodsHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('Method: %s' % self.request.method)

    delete = head = options = post = put = trace = get


class BrokenHandler(RequestHandler):
    def get(self, **kwargs):
        raise ValueError('booo!')


class BrokenButFixedHandler(BrokenHandler):
    def handle_exception(self, exception=None):
        # Let's fix it.
        return Response('That was close!', status=200)


class Handle404(RequestHandler):
    def handle_exception(self, exception=None):
        return Response('404 custom handler', status=404)


class Handle405(RequestHandler):
    def handle_exception(self, exception=None):
        response = Response('405 custom handler', status=405)
        response.headers['Allow'] = 'GET'
        return response


class Handle500(RequestHandler):
    def handle_exception(self, exception=None):
        return Response('500 custom handler', status=500)


class TestRequestHandler(BaseTestCase):
    def test_200(self):
        app = Tipfy(rules=[Rule('/', name='home', handler=AllMethodsHandler)])
        client = app.get_test_client()

        for method in app.allowed_methods:
            response = client.open('/', method=method)
            self.assertEqual(response.status_code, 200, method)
            if method == 'HEAD':
                self.assertEqual(response.data, '')
            else:
                self.assertEqual(response.data, 'Method: %s' % method)

        # App Engine mode.
        self._set_dev_server_flag(True)
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Method: GET')

    def test_404(self):
        """No URL rules defined."""
        app = Tipfy()
        client = app.get_test_client()

        # Normal mode.
        response = client.get('/')
        self.assertEqual(response.status_code, 404)

        # Debug mode.
        app.debug = True
        response = client.get('/')
        self.assertEqual(response.status_code, 404)

    def test_500(self):
        """Handler import will fail."""
        app = Tipfy(rules=[Rule('/', name='home', handler='non.existent.handler')])
        client = app.get_test_client()

        # Normal mode.
        response = client.get('/')
        self.assertEqual(response.status_code, 500)

        # Debug mode.
        app.debug = True
        app.config['tipfy']['enable_debugger'] = False
        self.assertRaises(ImportError, client.get, '/')

    def test_501(self):
        """Method is not in app.allowed_methods."""
        app = Tipfy()
        client = app.get_test_client()

        # Normal mode.
        response = client.open('/', method='CONNECT')
        self.assertEqual(response.status_code, 501)

        # Debug mode.
        app.debug = True
        response = client.open('/', method='CONNECT')
        self.assertEqual(response.status_code, 501)

    def test_abort(self):
        class HandlerWithAbort(RequestHandler):
            def get(self, **kwargs):
                self.abort(kwargs.get('status_code'))

        app = Tipfy(rules=[
            Rule('/<int:status_code>', name='abort-me', handler=HandlerWithAbort),
        ])
        client = app.get_test_client()

        response = client.get('/400')
        self.assertEqual(response.status_code, 400)

        response = client.get('/403')
        self.assertEqual(response.status_code, 403)

        response = client.get('/404')
        self.assertEqual(response.status_code, 404)

    def test_get_config(self):
        app = Tipfy(rules=[
            Rule('/', name='home', handler=AllMethodsHandler),
        ], config = {
            'foo': {
                'bar': 'baz',
            }
        })
        with app.get_test_handler('/') as handler:
            self.assertEqual(handler.get_config('foo', 'bar'), 'baz')

    def test_handle_exception(self):
        app = Tipfy([
            Rule('/', handler=AllMethodsHandler, name='home'),
            Rule('/broken', handler=BrokenHandler, name='broken'),
            Rule('/broken-but-fixed', handler=BrokenButFixedHandler, name='broken-but-fixed'),
        ], debug=False)
        client = app.get_test_client()

        response = client.get('/broken')
        self.assertEqual(response.status_code, 500)

        response = client.get('/broken-but-fixed')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'That was close!')

    def test_redirect(self):
        class HandlerWithRedirect(RequestHandler):
            def get(self, **kwargs):
                return self.redirect('/')

        app = Tipfy(rules=[
            Rule('/', name='home', handler=AllMethodsHandler),
            Rule('/redirect-me', name='redirect', handler=HandlerWithRedirect),
        ])

        client = app.get_test_client()
        response = client.get('/redirect-me', follow_redirects=True)
        self.assertEqual(response.data, 'Method: GET')

    def test_redirect_empty(self):
        class HandlerWithRedirect(RequestHandler):
            def get(self, **kwargs):
                return self.redirect('/', empty=True)

        app = Tipfy(rules=[
            Rule('/', name='home', handler=AllMethodsHandler),
            Rule('/redirect-me', name='redirect', handler=HandlerWithRedirect),
        ])

        client = app.get_test_client()
        response = client.get('/redirect-me', follow_redirects=False)
        self.assertEqual(response.data, '')

    def test_redirect_to(self):
        class HandlerWithRedirectTo(RequestHandler):
            def get(self, **kwargs):
                return self.redirect_to('home')

        app = Tipfy(rules=[
            Rule('/', name='home', handler=AllMethodsHandler),
            Rule('/redirect-me', name='redirect', handler=HandlerWithRedirectTo),
        ])

        client = app.get_test_client()
        response = client.get('/redirect-me', follow_redirects=True)
        self.assertEqual(response.data, 'Method: GET')

    def test_redirect_to_empty(self):
        class HandlerWithRedirectTo(RequestHandler):
            def get(self, **kwargs):
                return self.redirect_to('home', _empty=True)

        app = Tipfy(rules=[
            Rule('/', name='home', handler=AllMethodsHandler),
            Rule('/redirect-me', name='redirect', handler=HandlerWithRedirectTo),
        ])

        client = app.get_test_client()
        response = client.get('/redirect-me', follow_redirects=False)
        self.assertEqual(response.data, '')

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
        app = Tipfy(rules=[
            Rule('/', name='home', handler=AllMethodsHandler),
            Rule('/about', name='about', handler='handlers.About'),
            Rule('/contact', name='contact', handler='handlers.Contact'),
        ])
        with app.get_test_handler('/') as handler:
            self.assertEqual(handler.url_for('home'), '/')
            self.assertEqual(handler.url_for('about'), '/about')
            self.assertEqual(handler.url_for('contact'), '/contact')

            # Extras
            self.assertEqual(handler.url_for('about', _anchor='history'), '/about#history')
            self.assertEqual(handler.url_for('about', _full=True), 'http://localhost/about')
            self.assertEqual(handler.url_for('about', _netloc='www.google.com'), 'http://www.google.com/about')
            self.assertEqual(handler.url_for('about', _scheme='https'), 'https://localhost/about')

    def test_store_instances(self):
        from tipfy.appengine.auth import AuthStore
        from tipfy.i18n import I18nStore
        from tipfy.sessions import SecureCookieSession

        app = Tipfy(rules=[
            Rule('/', name='home', handler=AllMethodsHandler),
        ], config={
            'tipfy.sessions': {
                'secret_key': 'secret',
            },
        })
        with app.get_test_handler('/') as handler:
            self.assertEqual(isinstance(handler.session, SecureCookieSession), True)
            self.assertEqual(isinstance(handler.auth, AuthStore), True)
            self.assertEqual(isinstance(handler.i18n, I18nStore), True)


class TestHandlerMiddleware(BaseTestCase):
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

    def test_handle_exception_2(self):
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

    def test_handle_exception_3(self):
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

    def test_handle_exception_with_app_error_handler(self):
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


class TestTipfy(BaseTestCase):
    def test_custom_error_handlers(self):
        app = Tipfy([
            Rule('/', handler=AllMethodsHandler, name='home'),
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

        res = client.put('/broken')
        self.assertEqual(res.status_code, 405)
        self.assertEqual(res.data, '405 custom handler')
        self.assertEqual(res.headers.get('Allow'), 'GET')

        res = client.get('/broken')
        self.assertEqual(res.status_code, 500)
        self.assertEqual(res.data, '500 custom handler')

    def test_store_classes(self):
        from tipfy.appengine.auth import AuthStore
        from tipfy.i18n import I18nStore
        from tipfy.sessions import SessionStore

        app = Tipfy()
        self.assertEqual(app.auth_store_class, AuthStore)
        self.assertEqual(app.i18n_store_class, I18nStore)
        self.assertEqual(app.session_store_class, SessionStore)

    def test_make_response(self):
        app = Tipfy()
        request = Request.from_values()

        # Empty.
        response = app.make_response(request)
        self.assertEqual(isinstance(response, app.response_class), True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, '')

        # From Response.
        response = app.make_response(request, Response('Hello, World!'))
        self.assertEqual(isinstance(response, app.response_class), True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Hello, World!')

        # From string.
        response = app.make_response(request, 'Hello, World!')
        self.assertEqual(isinstance(response, app.response_class), True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Hello, World!')

        # From tuple.
        response = app.make_response(request, 'Hello, World!', 404)
        self.assertEqual(isinstance(response, app.response_class), True)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, 'Hello, World!')

        # From None.
        self.assertRaises(ValueError, app.make_response, request, None)

    def test_dev_run(self):
        self._set_dev_server_flag(True)

        os.environ['APPLICATION_ID'] = 'my-app'
        os.environ['SERVER_SOFTWARE'] = 'Development'
        os.environ['SERVER_NAME'] = 'localhost'
        os.environ['SERVER_PORT'] = '8080'
        os.environ['REQUEST_METHOD'] = 'GET'

        app = Tipfy(rules=[
            Rule('/', name='home', handler=AllMethodsHandler),
        ], debug=True)

        app.run()
        self.assertEqual(sys.stdout.getvalue(), 'Status: 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: 11\r\n\r\nMethod: GET')

    def test_get_config(self):
        app = Tipfy(config={'tipfy': {'foo': 'bar'}})
        self.assertEqual(app.get_config('tipfy', 'foo'), 'bar')


class TestRequest(BaseTestCase):
    def test_json(self):
        class JsonHandler(RequestHandler):
            def get(self, **kwargs):
                return Response(self.request.json['foo'])

        app = Tipfy(rules=[
            Rule('/', name='home', handler=JsonHandler),
        ], debug=True)

        data = json_encode({'foo': 'bar'})
        client = app.get_test_client()
        response = client.get('/', content_type='application/json', data=data)
        self.assertEqual(response.data, 'bar')
