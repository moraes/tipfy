# -*- coding: utf-8 -*-
"""
    Tests for tipfy.routing
"""
import unittest
from nose.tools import raises

from _base import get_environ

import tipfy

def get_url_map():
    # Fake get_rules() for testing.
    rules = [
        tipfy.Rule('/', endpoint='home', handler='test.home:HomeHandler'),
        tipfy.Rule('/people/<string:username>', endpoint='profile',
            handler='test.profile:ProfileHandler'),
    ]

    return tipfy.Map(rules)


def get_app():
    return tipfy.WSGIApplication({
        'tipfy': {
            'url_map': get_url_map(),
        },
    })


class TestUrls(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    #===========================================================================
    # Rule
    #===========================================================================
    def test_rule_empty(self):
        rule = tipfy.Rule('/', endpoint='home', handler='test.home:HomeHandler')
        rule_2 = rule.empty()

        assert rule_2.handler == 'test.home:HomeHandler'
        assert rule_2.endpoint == 'home'

    def test_rule_empty_2(self):
        rule = tipfy.Rule('/', endpoint='home', handler='test.home:HomeHandler', defaults={'foo': 'bar'})
        rule_2 = rule.empty()

        assert rule_2.handler == 'test.home:HomeHandler'
        assert rule_2.endpoint == 'home'
        assert rule_2.defaults == {'foo': 'bar'}

    #===========================================================================
    # RegexConverter
    #===========================================================================
    def test_regex_converter(self):
        app = tipfy.WSGIApplication({'tipfy': {
            'url_map': tipfy.Map([
                tipfy.Rule('/<regex(".*"):path>', endpoint='home', handler='test.home:HomeHandler'),
            ]),
        },})
        environ = get_environ()

        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match('/foo', return_rule=True)

        assert 'path' in rule_args
        assert rule_args['path'] == 'foo'

        rule, rule_args = app.url_adapter.match('/foo/bar/baz', return_rule=True)
        assert rule_args['path'] == 'foo/bar/baz'


    #===========================================================================
    # URL match
    #===========================================================================
    def test_url_match(self):
        app = get_app()
        environ = get_environ()
        request = tipfy.Request(environ)
        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        assert rule.handler == 'test.home:HomeHandler'
        assert rule_args == {}

    def test_url_match2(self):
        app = get_app()
        environ = get_environ(path='/people/calvin')
        request = tipfy.Request(environ)
        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        assert rule.handler == 'test.profile:ProfileHandler'
        assert rule_args == {'username': 'calvin'}

    @raises(tipfy.NotFound)
    def test_not_found(self):
        app = get_app()
        environ = get_environ(path='/this-path-is-not-mapped')
        request = tipfy.Request(environ)
        app.url_adapter = app.url_map.bind_to_environ(environ)

        app.url_adapter.match(request.path, return_rule=True)

    #===========================================================================
    # url_for()
    #===========================================================================
    def test_url_for(self):
        app = get_app()
        environ = get_environ()
        app.url_adapter = app.url_map.bind_to_environ(environ)

        assert tipfy.url_for('home') == '/'

    def test_url_for2(self):
        app = get_app()
        environ = get_environ()
        app.url_adapter = app.url_map.bind_to_environ(environ)

        assert tipfy.url_for('profile', username='calvin') == '/people/calvin'
        assert tipfy.url_for('profile', username='hobbes') == '/people/hobbes'
        assert tipfy.url_for('profile', username='moe') == '/people/moe'

    def test_url_for_full(self):
        app = get_app()
        environ = get_environ()
        app.url_adapter = app.url_map.bind_to_environ(environ)

        host = 'http://%s' % environ['HTTP_HOST']
        assert tipfy.url_for('home', full=True) == host + '/'

    def test_url_for_full2(self):
        app = get_app()
        environ = get_environ()
        app.url_adapter = app.url_map.bind_to_environ(environ)
        host = 'http://%s' % environ['HTTP_HOST']

        assert tipfy.url_for('profile', username='calvin', full=True) == \
            host + '/people/calvin'
        assert tipfy.url_for('profile', username='hobbes', full=True) == \
            host + '/people/hobbes'
        assert tipfy.url_for('profile', username='moe', full=True) == \
            host + '/people/moe'
