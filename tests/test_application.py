import os
import unittest

from tipfy import (Request, RequestHandler, Response, Rule, Tipfy,
    make_wsgi_app, run_wsgi_app, ALLOWED_METHODS)


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
        # 'my-app' is set in the running app.yaml.
        self.assertEqual(app.app_id, 'my-app')

        os.environ['APPLICATION_ID'] = 'my-other-app'
        app = Tipfy()
        self.assertEqual(app.app_id, 'my-other-app')
        os.environ.pop('APPLICATION_ID')

    def test_version_id(self):
        app = Tipfy()
        self.assertEqual(app.version_id, '1')

        os.environ['CURRENT_VERSION_ID'] = 'testing'
        app = Tipfy()
        self.assertEqual(app.version_id, 'testing')
        os.environ.pop('CURRENT_VERSION_ID')


class TestHandleException(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None

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

class SillyTests(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None

        from os import environ
        for key in ['SERVER_NAME', 'SERVER_PORT', 'REQUEST_METHOD', 'SERVER_SOFTWARE']:
            if key in environ:
                del environ[key]

    def test_make_wsgi_app(self):
        app = make_wsgi_app(config={'tipfy': {
        }})

        assert isinstance(app, Tipfy)

    def test_make_wsgi_app2(self):
        app = make_wsgi_app(config={'tipfy': {
            'foo': 'bar'
        }})

        assert isinstance(app, Tipfy)
        assert app.config.get('tipfy', 'foo') == 'bar'

    def test_make_wsgi_app_with_middleware(self):
        def app_wrapper(environ, start_response):
            pass

        class AppMiddleware(object):
            def post_make_app(self, app):
                app.wsgi_app = app_wrapper

        app = make_wsgi_app(config={'tipfy': {
            'middleware': [AppMiddleware]
        }})

        self.assertEqual(app.wsgi_app, app_wrapper)

    def test_run_wsgi_app(self):
        """We aren't testing anything here."""
        from os import environ

        environ['SERVER_NAME'] = 'foo.com'
        environ['SERVER_PORT'] = '80'
        environ['REQUEST_METHOD'] = 'GET'

        rules = [Rule('/', handler='resources.handlers.HomeHandler', name='home')]
        app = make_wsgi_app(rules=rules, debug=True)
        run_wsgi_app(app)

    def test_run_wsgi_app_dev(self):
        """We aren't testing anything here."""
        from os import environ

        environ['SERVER_NAME'] = 'foo.com'
        environ['SERVER_PORT'] = '80'
        environ['REQUEST_METHOD'] = 'GET'
        environ['SERVER_SOFTWARE'] = 'Dev'

        rules = [Rule('/', handler='resources.handlers.HomeHandler', name='home')]
        app = make_wsgi_app(rules=rules, debug=True)
        run_wsgi_app(app)

    def test_run_wsgi_app_with_middleware(self):
        class AppMiddleware_2(object):
            pass

        from os import environ

        environ['SERVER_NAME'] = 'foo.com'
        environ['SERVER_PORT'] = '80'
        environ['REQUEST_METHOD'] = 'GET'

        rules = [Rule('/', handler='resources.handlers.HomeHandler', name='home')]
        app = make_wsgi_app(rules=rules, config={'tipfy': {
            'middleware': [AppMiddleware_2]
        }})

        run_wsgi_app(app)

    def test_ultimate_sys_path(self):
        """Mostly here to not be marked as uncovered."""
        from tipfy import _ULTIMATE_SYS_PATH, fix_sys_path
        fix_sys_path()

    def test_ultimate_sys_path2(self):
        """Mostly here to not be marked as uncovered."""
        from tipfy import _ULTIMATE_SYS_PATH, fix_sys_path
        _ULTIMATE_SYS_PATH = []
        fix_sys_path()

    def test_ultimate_sys_path3(self):
        """Mostly here to not be marked as uncovered."""
        import sys
        path = list(sys.path)
        sys.path = []

        from tipfy import _ULTIMATE_SYS_PATH, fix_sys_path
        _ULTIMATE_SYS_PATH = []
        fix_sys_path()

        sys.path = path
