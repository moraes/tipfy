import unittest

from tipfy import Tipfy, RequestHandler, Response
from tipfy.routing import HandlerPrefix, Router, Rule


class TestRouter(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_add(self):
        app = Tipfy()
        router = Router(app)
        self.assertEqual(len(list(router.map.iter_rules())), 0)

        router.add(Rule('/', name='home', handler='HomeHandler'))
        self.assertEqual(len(list(router.map.iter_rules())), 1)

        router.add([
            Rule('/about', name='about', handler='AboutHandler'),
            Rule('/contact', name='contact', handler='ContactHandler'),
        ])
        self.assertEqual(len(list(router.map.iter_rules())), 3)


class TestRouting(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    #==========================================================================
    # HandlerPrefix
    #==========================================================================
    def test_handler_prefix(self):
        rules = [
            HandlerPrefix('resources.handlers.', [
                Rule('/', name='home', handler='HomeHandler'),
                Rule('/defaults', name='defaults', handler='HandlerWithRuleDefaults', defaults={'foo': 'bar'}),
            ])
        ]

        app = Tipfy(rules)
        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'Hello, World!')

        response = client.get('/defaults')
        self.assertEqual(response.data, 'bar')

    #==========================================================================
    # RegexConverter
    #==========================================================================
    def test_regex_converter(self):
        class TestHandler(RequestHandler):
            def get(self, **kwargs):
                return Response(kwargs.get('path'))

        app = Tipfy([
            Rule('/<regex(".*"):path>', name='home', handler=TestHandler),
        ])

        client = app.get_test_client()

        response = client.get('/foo')
        self.assertEqual(response.data, 'foo')

        response = client.get('/foo/bar')
        self.assertEqual(response.data, 'foo/bar')

        response = client.get('/foo/bar/baz')
        self.assertEqual(response.data, 'foo/bar/baz')


class TestAlternativeRouting(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    #==========================================================================
    # HandlerPrefix
    #==========================================================================
    def test_handler(self):
        rules = [
            HandlerPrefix('resources.alternative_routing.', [
                Rule('/', name='home', handler='HomeHandler'),
                Rule('/foo', name='home/foo', handler='HomeHandler:foo'),
                Rule('/bar', name='home/bar', handler='HomeHandler:bar'),
                Rule('/other/foo', name='other/foo', handler='OtherHandler:foo'),
                Rule('/other/bar', name='other/bar', handler='OtherHandler:bar'),
            ])
        ]

        app = Tipfy(rules)
        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'home-get')
        response = client.get('/foo')
        self.assertEqual(response.data, 'home-foo')
        response = client.get('/bar')
        self.assertEqual(response.data, 'home-bar')
        response = client.get('/other/foo')
        self.assertEqual(response.data, 'other-foo')
        response = client.get('/other/bar')
        self.assertEqual(response.data, 'other-bar')
