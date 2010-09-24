# -*- coding: utf-8 -*-
"""
    Tests for tipfy utils
"""
import unittest

import werkzeug

from tipfy import (RequestHandler, Response, Rule, Tipfy, redirect,
    redirect_to, render_json_response)

from tipfy.utils import (xhtml_escape, xhtml_unescape, json_encode,
    json_decode, url_escape, url_unescape, utf8, _unicode)


class HomeHandler(RequestHandler):
    def get(self, **kwargs):
        return 'Hello, World!'


class ProfileHandler(RequestHandler):
    def get(self, **kwargs):
        return 'Username: %s' % kwargs.get('username')


class RedirectToHandler(RequestHandler):
    def get(self, **kwargs):
        username = kwargs.get('username', None)
        if username:
            return redirect_to('profile', username=username)
        else:
            return redirect_to('home')


class RedirectTo301Handler(RequestHandler):
    def get(self, **kwargs):
        username = kwargs.get('username', None)
        if username:
            return redirect_to('profile', username=username, _code=301)
        else:
            return redirect_to('home', _code=301)


class RedirectToInvalidCodeHandler(RequestHandler):
    def get(self, **kwargs):
        return redirect_to('home', _code=405)


def get_app():
    return Tipfy(rules=[
        Rule('/', name='home', handler=HomeHandler),
        Rule('/people/<string:username>', name='profile', handler=ProfileHandler),
        Rule('/redirect_to/', name='redirect_to', handler=RedirectToHandler),
        Rule('/redirect_to/<string:username>', name='redirect_to', handler=RedirectToHandler),
        Rule('/redirect_to_301/', name='redirect_to', handler=RedirectTo301Handler),
        Rule('/redirect_to_301/<string:username>', name='redirect_to', handler=RedirectTo301Handler),
        Rule('/redirect_to_invalid', name='redirect_to_invalid', handler=RedirectToInvalidCodeHandler),
    ])


class TestRedirect(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

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

    def test_redirect_invalid_code(self):
        self.assertRaises(AssertionError, redirect, 'http://www.google.com/', 404)

    #===========================================================================
    # redirect_to()
    #===========================================================================
    def test_redirect_to(self):
        app = get_app()
        client = app.get_test_client()

        response = client.get('/redirect_to/', base_url='http://foo.com')
        assert response.headers['location'] == 'http://foo.com/'
        assert response.status_code == 302


    def test_redirect_to2(self):
        app = get_app()
        client = app.get_test_client()

        response = client.get('/redirect_to/calvin', base_url='http://foo.com')
        assert response.headers['location'] == 'http://foo.com/people/calvin'
        assert response.status_code == 302

        response = client.get('/redirect_to/hobbes', base_url='http://foo.com')
        assert response.headers['location'] == 'http://foo.com/people/hobbes'
        assert response.status_code == 302

        response = client.get('/redirect_to/moe', base_url='http://foo.com')
        assert response.headers['location'] == 'http://foo.com/people/moe'
        assert response.status_code == 302

    def test_redirect_to_301(self):
        app = get_app()
        client = app.get_test_client()

        response = client.get('/redirect_to_301/calvin', base_url='http://foo.com')
        assert response.headers['location'] == 'http://foo.com/people/calvin'
        assert response.status_code == 301

        response = client.get('/redirect_to_301/hobbes', base_url='http://foo.com')
        assert response.headers['location'] == 'http://foo.com/people/hobbes'
        assert response.status_code == 301

        response = client.get('/redirect_to_301/moe', base_url='http://foo.com')
        assert response.headers['location'] == 'http://foo.com/people/moe'
        assert response.status_code == 301

    def test_redirect_to_invalid_code(self):
        app = get_app()
        client = app.get_test_client()

        response = client.get('/redirect_to_invalid', base_url='http://foo.com')
        assert response.status_code == 500


class TestRenderJson(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    #===========================================================================
    # render_json_response()
    #===========================================================================
    def test_render_json_response(self):
        response = render_json_response({'foo': 'bar'})

        assert isinstance(response, Response)
        assert response.mimetype == 'application/json'
        assert response.data == '{"foo": "bar"}'


class TestUtils(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_xhtml_escape(self):
        self.assertEqual(xhtml_escape('"foo"'), '&quot;foo&quot;')

    def test_xhtml_unescape(self):
        self.assertEqual(xhtml_unescape('&quot;foo&quot;'), '"foo"')

    def test_json_encode(self):
        self.assertEqual(json_encode('<script>alert("hello")</script>'), '"<script>alert(\\"hello\\")<\\/script>"')

    def test_json_decode(self):
        self.assertEqual(json_decode('"<script>alert(\\"hello\\")<\\/script>"'), '<script>alert("hello")</script>')

    def test_url_escape(self):
        self.assertEqual(url_escape('somewords&some more words'), 'somewords%26some+more+words')

    def test_url_unescape(self):
        self.assertEqual(url_unescape('somewords%26some+more+words'), 'somewords&some more words')

    def test_utf8(self):
        self.assertEqual(isinstance(utf8(u'ááá'), str), True)
        self.assertEqual(isinstance(utf8('ááá'), str), True)

    def test_unicode(self):
        self.assertEqual(isinstance(_unicode(u'ááá'), unicode), True)
        self.assertEqual(isinstance(_unicode('ááá'), unicode), True)
