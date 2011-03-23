from __future__ import with_statement

from . import BaseTestCase

from tipfy import Tipfy, RequestHandler, Response
from tipfy.routing import HandlerPrefix, NamePrefix, Router, Rule


class TestRouter(BaseTestCase):
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


class TestRouting(BaseTestCase):
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
    # NamePrefix
    #==========================================================================
    def test_name_prefix(self):
        class DummyHandler(RequestHandler):
            def get(self, **kwargs):
                return ''

        rules = [
            NamePrefix('company-', [
                Rule('/', name='home', handler=DummyHandler),
                Rule('/about', name='about', handler=DummyHandler),
                Rule('/contact', name='contact', handler=DummyHandler),
            ]),
        ]

        app = Tipfy(rules)

        with app.get_test_handler('/') as handler:
            self.assertEqual(handler.url_for('company-home'), '/')
            self.assertEqual(handler.url_for('company-about'), '/about')
            self.assertEqual(handler.url_for('company-contact'), '/contact')

        with app.get_test_handler('/') as handler:
            self.assertEqual(handler.request.rule.name, 'company-home')

        with app.get_test_handler('/about') as handler:
            self.assertEqual(handler.request.rule.name, 'company-about')

        with app.get_test_handler('/contact') as handler:
            self.assertEqual(handler.request.rule.name, 'company-contact')

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


class TestAlternativeRouting(BaseTestCase):
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

    def test_function_handler(self):
        rules = [
            HandlerPrefix('resources.alternative_routing.', [
                Rule('/', name='home', handler='home'),
                Rule('/foo', name='home/foo', handler='foo'),
                Rule('/bar', name='home/bar', handler='bar'),
            ])
        ]

        app = Tipfy(rules)
        client = app.get_test_client()

        response = client.get('/')
        self.assertEqual(response.data, 'home')
        response = client.get('/foo')
        self.assertEqual(response.data, 'foo')
        response = client.get('/bar')
        self.assertEqual(response.data, 'bar')
