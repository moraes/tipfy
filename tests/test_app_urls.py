# -*- coding: utf-8 -*-
"""
    Tests for tipfy's URL related functions: matching URLs, url_for(),
    redirect(), redirect_to().
"""
import unittest
from nose.tools import raises

import werkzeug

from _base import get_environ
from tipfy import local, redirect, redirect_to, url_for, NotFound, Rule
import tipfy

def get_url_map():
    # Fake get_rules() for testing.
    rules = [
        Rule('/', endpoint='home', handler='test.home:HomeHandler'),
        Rule('/people/<string:username>', endpoint='profile',
            handler='test.profile:ProfileHandler'),
    ]

    return werkzeug.routing.Map(rules)


def get_app_environ_request(**kwargs):
    app = tipfy.WSGIApplication({
        'tipfy': {
            'url_map': get_url_map(),
        },
    })
    environ = get_environ(**kwargs)
    request = werkzeug.Request(environ)
    return app, environ, request


class TestUrls(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    #===========================================================================
    # URL match
    #===========================================================================
    def test_url_match(self):
        app, environ, request = get_app_environ_request()
        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        assert rule.handler == 'test.home:HomeHandler'
        assert rule_args == {}

    def test_url_match2(self):
        app, environ, request = get_app_environ_request(path='/people/calvin')
        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        assert rule.handler == 'test.profile:ProfileHandler'
        assert rule_args == {'username': 'calvin'}

    @raises(NotFound)
    def test_not_found(self):
        app, environ, request = get_app_environ_request(
            path='/this-path-is-not-mapped')
        app.url_adapter = app.url_map.bind_to_environ(environ)

        app.url_adapter.match(request.path, return_rule=True)

    #===========================================================================
    # url_for()
    #===========================================================================
    def test_url_for(self):
        app, environ, request = get_app_environ_request()
        app.url_adapter = app.url_map.bind_to_environ(environ)

        assert url_for('home') == '/'

    def test_url_for2(self):
        app, environ, request = get_app_environ_request()
        app.url_adapter = app.url_map.bind_to_environ(environ)

        assert url_for('profile', username='calvin') == '/people/calvin'
        assert url_for('profile', username='hobbes') == '/people/hobbes'
        assert url_for('profile', username='moe') == '/people/moe'

    def test_url_for_full(self):
        app, environ, request = get_app_environ_request()
        app.url_adapter = app.url_map.bind_to_environ(environ)

        host = 'http://%s' % environ['HTTP_HOST']
        assert url_for('home', full=True) == host + '/'

    def test_url_for_full2(self):
        app, environ, request = get_app_environ_request()
        app.url_adapter = app.url_map.bind_to_environ(environ)
        host = 'http://%s' % environ['HTTP_HOST']

        assert url_for('profile', username='calvin', full=True) == \
            host + '/people/calvin'
        assert url_for('profile', username='hobbes', full=True) == \
            host + '/people/hobbes'
        assert url_for('profile', username='moe', full=True) == \
            host + '/people/moe'

    #===========================================================================
    # redirect_to()
    #===========================================================================
    def test_redirect_to(self):
        app, environ, request = get_app_environ_request()
        local.response = werkzeug.Response()
        app.url_adapter = app.url_map.bind_to_environ(environ)
        host = 'http://%s' % environ['HTTP_HOST']

        response = redirect_to('home')
        assert response.headers['location'] == host + '/'
        assert response.status_code == 302

    def test_redirect_to2(self):
        app, environ, request = get_app_environ_request()
        local.response = werkzeug.Response()
        app.url_adapter = app.url_map.bind_to_environ(environ)
        host = 'http://%s' % environ['HTTP_HOST']

        response = redirect_to('profile', username='calvin')
        assert response.headers['location'] == host + '/people/calvin'
        assert response.status_code == 302

        response = redirect_to('profile', username='hobbes')
        assert response.headers['location'] == host + '/people/hobbes'
        assert response.status_code == 302

        response = redirect_to('profile', username='moe')
        assert response.headers['location'] == host + '/people/moe'
        assert response.status_code == 302

    def test_redirect_to_301(self):
        app, environ, request = get_app_environ_request()
        local.response = werkzeug.Response()
        app.url_adapter = app.url_map.bind_to_environ(environ)
        host = 'http://%s' % environ['HTTP_HOST']

        response = redirect_to('home', code=301)
        assert response.headers['location'] == host + '/'
        assert response.status_code == 301

    @raises(AssertionError)
    def test_redirect_to_invalid_code(self):
        app, environ, request = get_app_environ_request()
        local.response = werkzeug.Response()
        app.url_adapter = app.url_map.bind_to_environ(environ)

        redirect_to('home', code=405)

    #===========================================================================
    # redirect()
    #===========================================================================
    def test_redirect(self):
        local.response = werkzeug.Response()
        response = redirect('http://www.google.com/')

        assert response == local.response
        assert response.headers['location'] == 'http://www.google.com/'
        assert response.status_code == 302

    def test_redirect_301(self):
        local.response = werkzeug.Response()
        response = redirect('http://www.google.com/', 301)

        assert response == local.response
        assert response.headers['location'] == 'http://www.google.com/'
        assert response.status_code == 301

    def test_redirect_no_response(self):
        response = redirect('http://www.google.com/')

        assert isinstance(response, werkzeug.Response)
        assert response.headers['location'] == 'http://www.google.com/'
        assert response.status_code == 302

    def test_redirect_no_response_301(self):
        response = redirect('http://www.google.com/', 301)

        assert isinstance(response, werkzeug.Response)
        assert response.headers['location'] == 'http://www.google.com/'
        assert response.status_code == 301

    @raises(AssertionError)
    def test_redirect_invalid_code(self):
        local.response = werkzeug.Response()

        redirect('http://www.google.com/', 404)
