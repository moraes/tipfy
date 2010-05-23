# -*- coding: utf-8 -*-
"""
    Tests for tipfy.utils
"""
import unittest
from nose.tools import raises

import _base

import werkzeug

from tipfy import (local, Map, normalize_callable, redirect, redirect_to,
    render_json_response, Request, Response, Rule, WSGIApplication)


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


class TestUtils(unittest.TestCase):
    def tearDown(self):
        local.__release_local__()

    #===========================================================================
    # normalize_callable()
    #===========================================================================
    def test_normalize_callable_string(self):
        my_callable = normalize_callable('tipfy.WSGIApplication')
        assert my_callable is WSGIApplication

    def test_normalize_callable_callable(self):
        my_callable = normalize_callable(WSGIApplication)
        assert my_callable is WSGIApplication

    @raises(ValueError)
    def test_normalize_callable_not_callable(self):
        my_callable = normalize_callable('tipfy.default_config')

    @raises(ImportError)
    def test_normalize_callable_import_error(self):
        my_callable = normalize_callable('foo.bar.i_dont_exist')

    @raises(AttributeError)
    def test_normalize_callable_attribute_error(self):
        my_callable = normalize_callable('tipfy.i_dont_exist')

    #===========================================================================
    # redirect()
    #===========================================================================
    def test_redirect(self):
        response = redirect('http://www.google.com/')

        assert response.headers['location'] == 'http://www.google.com/'
        assert response.status_code == 302

    def test_redirect_301(self):
        response = redirect('http://www.google.com/', 301)

        assert response.headers['location'] == 'http://www.google.com/'
        assert response.status_code == 301

    def test_redirect_no_response(self):
        response = redirect('http://www.google.com/')

        assert isinstance(response, werkzeug.BaseResponse)
        assert response.headers['location'] == 'http://www.google.com/'
        assert response.status_code == 302

    def test_redirect_no_response_301(self):
        response = redirect('http://www.google.com/', 301)

        assert isinstance(response, werkzeug.BaseResponse)
        assert response.headers['location'] == 'http://www.google.com/'
        assert response.status_code == 301

    @raises(AssertionError)
    def test_redirect_invalid_code(self):
        redirect('http://www.google.com/', 404)

    #===========================================================================
    # redirect_to()
    #===========================================================================
    def test_redirect_to(self):
        host = 'http://foo.com'
        local.request = Request.from_values(base_url=host)
        app = get_app()
        app.match_url(local.request)

        response = redirect_to('home')
        assert response.headers['location'] == host + '/'
        assert response.status_code == 302

    def test_redirect_to2(self):
        host = 'http://foo.com'
        local.request = Request.from_values(base_url=host)
        app = get_app()
        app.match_url(local.request)

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
        host = 'http://foo.com'
        local.request = Request.from_values(base_url=host)
        app = get_app()
        app.match_url(local.request)

        response = redirect_to('home', code=301)
        assert response.headers['location'] == host + '/'
        assert response.status_code == 301

    @raises(AssertionError)
    def test_redirect_to_invalid_code(self):
        host = 'http://foo.com'
        local.request = Request.from_values(base_url=host)
        app = get_app()
        app.match_url(local.request)

        redirect_to('home', code=405)

    #===========================================================================
    # render_json_response()
    #===========================================================================
    def test_render_json_response(self):
        response = render_json_response({'foo': 'bar'})

        assert isinstance(response, Response)
        assert response.mimetype == 'application/json'
        assert response.data == '{"foo": "bar"}'
