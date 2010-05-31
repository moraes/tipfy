# -*- coding: utf-8 -*-
"""
    Tests for tipfy utils
"""
import unittest
from nose.tools import raises

import werkzeug

try:
    from tipfy import (Map, normalize_callable, redirect, redirect_to,
        render_json_response, Request, Response, Rule, Tipfy)
except ImportError:
    import sys
    res = ''
    if 'tipfy' in sys.modules:
        res = '=' * 100
        res += '\n'
        res += sys.modules['tipfy'].__file__
        res += '\n'
        res += '=' * 100

    sys.exit(res)

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


class TestUtils(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    #===========================================================================
    # normalize_callable()
    #===========================================================================
    def test_normalize_callable_string(self):
        my_callable = normalize_callable('tipfy.Tipfy')
        assert my_callable is Tipfy

    def test_normalize_callable_callable(self):
        my_callable = normalize_callable(Tipfy)
        assert my_callable is Tipfy

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
        app = get_app()
        request = get_request(app, base_url='http://foo.com')
        app.match_url(request)

        response = redirect_to('home')
        assert response.headers['location'] == 'http://foo.com/'
        assert response.status_code == 302

    def test_redirect_to2(self):
        app = get_app()
        request = get_request(app, base_url='http://foo.com')
        app.match_url(request)

        response = redirect_to('profile', username='calvin')
        assert response.headers['location'] == 'http://foo.com/people/calvin'
        assert response.status_code == 302

        response = redirect_to('profile', username='hobbes')
        assert response.headers['location'] == 'http://foo.com/people/hobbes'
        assert response.status_code == 302

        response = redirect_to('profile', username='moe')
        assert response.headers['location'] == 'http://foo.com/people/moe'
        assert response.status_code == 302

    def test_redirect_to_301(self):
        app = get_app()
        request = get_request(app, base_url='http://foo.com')
        app.match_url(request)

        response = redirect_to('home', code=301)
        assert response.headers['location'] == 'http://foo.com/'
        assert response.status_code == 301

    @raises(AssertionError)
    def test_redirect_to_invalid_code(self):
        app = get_app()
        request = get_request(app, base_url='http://foo.com')
        app.match_url(request)

        redirect_to('home', code=405)

    #===========================================================================
    # render_json_response()
    #===========================================================================
    def test_render_json_response(self):
        response = render_json_response({'foo': 'bar'})

        assert isinstance(response, Response)
        assert response.mimetype == 'application/json'
        assert response.data == '{"foo": "bar"}'
