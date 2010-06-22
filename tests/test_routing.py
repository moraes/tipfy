# -*- coding: utf-8 -*-
"""
    Tests for tipfy routing
"""
import unittest
from nose.tools import raises

from tipfy import (Map, NotFound, Request, Rule, Tipfy, url_for)


def get_url_map():
    # Fake get_rules() for testing.
    rules = [
        Rule('/', endpoint='home', handler='test.home:HomeHandler'),
        Rule('/people/<string:username>', endpoint='profile',
            handler='test.profile:ProfileHandler'),
    ]

    return Map(rules)


def get_app():
    app = Tipfy({
        'tipfy': {
            'url_map': get_url_map(),
        },
    })
    app.set_wsgi_app()
    return app


def get_request(app, *args, **kwargs):
    request = Request.from_values(*args, **kwargs)
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
        request = get_request(app, base_url='http://foo.com')
        app.match_url(request)

        assert request.rule.handler == 'test.home:HomeHandler'
        assert request.rule_args == {}

    def test_url_match2(self):
        app = get_app()
        request = get_request(app, base_url='http://foo.com', path='/people/calvin')
        app.match_url(request)

        assert request.rule.handler == 'test.profile:ProfileHandler'
        assert request.rule_args == {'username': 'calvin'}

    def test_not_found(self):
        app = get_app()
        request = get_request(app, base_url='http://foo.com', path='/this-path-is-not-mapped')
        app.match_url(request)

        assert isinstance(request.routing_exception, NotFound)

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
