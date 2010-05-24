# -*- coding: utf-8 -*-
"""
    Tests for tipfy.routing
"""
import unittest
from nose.tools import raises

import _base

from tipfy import (cleanup_wsgi_app, local, Map, NotFound, Request, Rule,
    set_request, url_for, WSGIApplication)

def get_url_map():
    # Fake get_rules() for testing.
    rules = [
        Rule('/', endpoint='home', handler='test.home:HomeHandler'),
        Rule('/people/<string:username>', endpoint='profile',
            handler='test.profile:ProfileHandler'),
    ]

    return Map(rules)


def get_app():
    return WSGIApplication({
        'tipfy': {
            'url_map': get_url_map(),
        },
    })


class TestUrls(unittest.TestCase):
    def tearDown(self):
        cleanup_wsgi_app()

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
    # RegexConverter
    #===========================================================================
    def test_regex_converter(self):
        host = 'http://foo.com'
        request = Request.from_values(base_url=host, path='/foo')
        set_request(request)
        app = WSGIApplication({'tipfy': {
            'url_map': Map([
                Rule('/<regex(".*"):path>', endpoint='home',
                    handler='test.home:HomeHandler'),
            ]),
        },})
        app.match_url(request)
        rule, rule_args = request.rule, request.rule_args

        assert 'path' in rule_args
        assert rule_args['path'] == 'foo'

    def test_regex_converter2(self):
        host = 'http://foo.com'
        request = Request.from_values(base_url=host, path='/foo/bar/baz')
        set_request(request)
        app = WSGIApplication({'tipfy': {
            'url_map': Map([
                Rule('/<regex(".*"):path>', endpoint='home',
                    handler='test.home:HomeHandler'),
            ]),
        },})
        app.match_url(request)
        rule, rule_args = request.rule, request.rule_args

        assert rule_args['path'] == 'foo/bar/baz'


    #===========================================================================
    # URL match
    #===========================================================================
    def test_url_match(self):
        request = Request.from_values(base_url='http://foo.com')
        set_request(request)
        app = get_app()
        app.match_url(request)

        assert request.rule.handler == 'test.home:HomeHandler'
        assert request.rule_args == {}

    def test_url_match2(self):
        request = Request.from_values(base_url='http://foo.com', path='/people/calvin')
        set_request(request)
        app = get_app()
        app.match_url(request)

        assert request.rule.handler == 'test.profile:ProfileHandler'
        assert request.rule_args == {'username': 'calvin'}

    def test_not_found(self):
        request = Request.from_values(base_url='http://foo.com', path='/this-path-is-not-mapped')
        set_request(request)
        app = get_app()
        app.match_url(request)

        assert isinstance(request.routing_exception, NotFound)

    #===========================================================================
    # url_for()
    #===========================================================================
    def test_url_for(self):
        host = 'http://foo.com'
        request = Request.from_values(base_url=host)
        set_request(request)
        app = get_app()
        app.match_url(request)

        assert url_for('home') == '/'

    def test_url_for2(self):
        host = 'http://foo.com'
        request = Request.from_values(base_url=host)
        set_request(request)
        app = get_app()
        app.match_url(request)

        assert url_for('profile', username='calvin') == '/people/calvin'
        assert url_for('profile', username='hobbes') == '/people/hobbes'
        assert url_for('profile', username='moe') == '/people/moe'

    def test_url_for_full(self):
        host = 'http://foo.com'
        request = Request.from_values(base_url=host)
        set_request(request)
        app = get_app()
        app.match_url(request)

        assert url_for('home', full=True) == host + '/'

    def test_url_for_full2(self):
        host = 'http://foo.com'
        request = Request.from_values(base_url=host)
        set_request(request)
        app = get_app()
        app.match_url(request)

        assert url_for('profile', username='calvin', full=True) == \
            host + '/people/calvin'
        assert url_for('profile', username='hobbes', full=True) == \
            host + '/people/hobbes'
        assert url_for('profile', username='moe', full=True) == \
            host + '/people/moe'

    def test_url_for_with_anchor(self):
        request = Request.from_values(base_url='http://foo.com')
        set_request(request)
        app = get_app()
        app.match_url(request)

        assert url_for('home', _anchor='my-little-anchor') == '/#my-little-anchor'
        assert url_for('home', _full=True, _anchor='my-little-anchor') == 'http://foo.com/#my-little-anchor'
