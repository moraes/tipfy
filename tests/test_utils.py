# -*- coding: utf-8 -*-
"""
    Tests for tipfy.utils
"""
import unittest
from nose.tools import raises

import _base

import werkzeug

import tipfy
from tipfy import utils


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


class TestUtils(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    #===========================================================================
    # normalize_callable()
    #===========================================================================
    def test_normalize_callable_string(self):
        my_callable = utils.normalize_callable('tipfy.WSGIApplication')
        assert my_callable is tipfy.WSGIApplication

    def test_normalize_callable_callable(self):
        my_callable = utils.normalize_callable(tipfy.WSGIApplication)
        assert my_callable is tipfy.WSGIApplication

    @raises(ValueError)
    def test_normalize_callable_not_callable(self):
        my_callable = utils.normalize_callable('tipfy.default_config')

    @raises(ImportError)
    def test_normalize_callable_import_error(self):
        my_callable = utils.normalize_callable('foo.bar.i_dont_exist')

    @raises(AttributeError)
    def test_normalize_callable_attribute_error(self):
        my_callable = utils.normalize_callable('tipfy.i_dont_exist')

    #===========================================================================
    # redirect()
    #===========================================================================
    def test_redirect(self):
        response = utils.redirect('http://www.google.com/')

        assert response.headers['location'] == 'http://www.google.com/'
        assert response.status_code == 302

    def test_redirect_301(self):
        response = utils.redirect('http://www.google.com/', 301)

        assert response.headers['location'] == 'http://www.google.com/'
        assert response.status_code == 301

    def test_redirect_no_response(self):
        response = utils.redirect('http://www.google.com/')

        assert isinstance(response, werkzeug.BaseResponse)
        assert response.headers['location'] == 'http://www.google.com/'
        assert response.status_code == 302

    def test_redirect_no_response_301(self):
        response = utils.redirect('http://www.google.com/', 301)

        assert isinstance(response, werkzeug.BaseResponse)
        assert response.headers['location'] == 'http://www.google.com/'
        assert response.status_code == 301

    @raises(AssertionError)
    def test_redirect_invalid_code(self):
        utils.redirect('http://www.google.com/', 404)

    #===========================================================================
    # redirect_to()
    #===========================================================================
    def test_redirect_to(self):
        app = get_app()
        app.url_adapter = app.url_map.bind('foo.com')
        host = 'http://foo.com'

        response = utils.redirect_to('home')
        assert response.headers['location'] == host + '/'
        assert response.status_code == 302

    def test_redirect_to2(self):
        app = get_app()
        app.url_adapter = app.url_map.bind('foo.com')
        host = 'http://foo.com'

        response = utils.redirect_to('profile', username='calvin')
        assert response.headers['location'] == host + '/people/calvin'
        assert response.status_code == 302

        response = utils.redirect_to('profile', username='hobbes')
        assert response.headers['location'] == host + '/people/hobbes'
        assert response.status_code == 302

        response = utils.redirect_to('profile', username='moe')
        assert response.headers['location'] == host + '/people/moe'
        assert response.status_code == 302

    def test_redirect_to_301(self):
        app = get_app()
        app.url_adapter = app.url_map.bind('foo.com')
        host = 'http://foo.com'

        response = utils.redirect_to('home', code=301)
        assert response.headers['location'] == host + '/'
        assert response.status_code == 301

    @raises(AssertionError)
    def test_redirect_to_invalid_code(self):
        app = get_app()
        app.url_adapter = app.url_map.bind('foo.com')

        utils.redirect_to('home', code=405)

    #===========================================================================
    # render_json_response()
    #===========================================================================
    def test_render_json_response(self):
        response = utils.render_json_response({'foo': 'bar'})

        assert isinstance(response, tipfy.Response)
        assert response.mimetype == 'application/json'
        assert response.data == '{"foo": "bar"}'
