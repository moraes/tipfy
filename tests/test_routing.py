# -*- coding: utf-8 -*-
"""
    Tests for tipfy routing
"""
import unittest
from nose.tools import raises

from tipfy import (HandlerPrefix, Request, RequestHandler, Response, Rule,
    Tipfy, url_for)


class HomeHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('Hello, World!')


class ProfileHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('Username: %s' % kwargs.get('username'))


def get_app():
    return Tipfy(rules=[
        Rule('/', endpoint='home', handler=HomeHandler),
        Rule('/people/<string:username>', endpoint='profile', handler=ProfileHandler),
    ])


def get_request(app, **kwargs):
    request = Request.from_values(**kwargs)
    app.set_request(request)
    return request


class TestUrls(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    #===========================================================================
    # Rule
    #===========================================================================
    def test_rule_empty(self):
        rule = Rule('/', endpoint='home', handler='test.home:HomeHandler')
        rule_2 = rule.empty()

        assert rule_2.handler == 'test.home:HomeHandler'
        assert rule_2.endpoint == 'home'

    def test_rule_empty_2(self):
        rule = Rule('/', endpoint='home', handler='test.home:HomeHandler',
            defaults={'foo': 'bar'})
        rule_2 = rule.empty()

        assert rule_2.handler == 'test.home:HomeHandler'
        assert rule_2.endpoint == 'home'
        assert rule_2.defaults == {'foo': 'bar'}

    #===========================================================================
    # URL match
    #===========================================================================
    def test_url_match(self):
        app = get_app()
        client = app.get_test_client()

        response = client.get('/')
        assert response.status_code == 200
        assert response.data == 'Hello, World!'

    def test_url_match2(self):
        app = get_app()
        client = app.get_test_client()

        response = client.get('/people/calvin')
        assert response.status_code == 200
        assert response.data == 'Username: calvin'

    def test_not_found(self):
        app = get_app()
        client = app.get_test_client()

        response = client.get('/this-path-is-not-mapped')
        assert response.status_code == 404

    #===========================================================================
    # url_for()
    #===========================================================================
    def test_url_for(self):
        app = get_app()
        request = get_request(app, base_url='http://foo.com')
        app.match_url(request)

        assert url_for('home') == '/'

    def test_url_for2(self):
        app = get_app()
        request = get_request(app, base_url='http://foo.com')
        app.match_url(request)

        assert url_for('profile', username='calvin') == '/people/calvin'
        assert url_for('profile', username='hobbes') == '/people/hobbes'
        assert url_for('profile', username='moe') == '/people/moe'

    def test_url_for_full(self):
        app = get_app()
        request = get_request(app, base_url='http://foo.com')
        app.match_url(request)

        assert url_for('home', full=True) == 'http://foo.com/'

    def test_url_for_full2(self):
        app = get_app()
        request = get_request(app, base_url='http://foo.com')
        app.match_url(request)

        assert url_for('profile', username='calvin', full=True) == \
            'http://foo.com/people/calvin'
        assert url_for('profile', username='hobbes', full=True) == \
            'http://foo.com/people/hobbes'
        assert url_for('profile', username='moe', full=True) == \
            'http://foo.com/people/moe'

    def test_url_for_with_anchor(self):
        app = get_app()
        request = get_request(app, base_url='http://foo.com')
        app.match_url(request)

        assert url_for('home', _anchor='my-little-anchor') == '/#my-little-anchor'
        assert url_for('home', _full=True, _anchor='my-little-anchor') == 'http://foo.com/#my-little-anchor'


class TestHandlerPrefix(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_get_rules(self):
        rule = HandlerPrefix('myapp.my.module.', [
            Rule('/', endpoint='home', handler='HomeHandler'),
            Rule('/users', endpoint='users', handler='UsersHandler'),
            Rule('/contact', endpoint='contact', handler='ContactHandler'),
        ])

        rules = list(rule.get_rules(None))
        self.assertEqual(len(rules), 3)
        self.assertEqual(rules[0].handler, 'myapp.my.module.HomeHandler')
        self.assertEqual(rules[1].handler, 'myapp.my.module.UsersHandler')
        self.assertEqual(rules[2].handler, 'myapp.my.module.ContactHandler')
