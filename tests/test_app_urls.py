# -*- coding: utf-8 -*-
"""
    Tests for tipfy's url related functions: matching URLs, url_for(),
    redirect(), redirect_to().
"""
import unittest
import sys
from _base import get_app, get_environ, get_request, get_response


def get_rules():
    # Fake get_rules() for testing.
    from tipfy import Rule
    return [
        Rule('/', endpoint='home', handler='test.home:HomeHandler'),
        Rule('/people/<string:username>', endpoint='profile', handler='test.profile:ProfileHandler'),
    ]


class TestUrl(unittest.TestCase):
    def setUp(self):
        # Make it load our test url rules.
        sys.modules['urls'] = sys.modules[__name__]

    def tearDown(self):
        if 'urls' in sys.modules:
            del sys.modules['urls']

    def test_url_match(self):
        app = get_app()
        environ = get_environ()
        request = get_request(environ)

        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        self.assertEqual(rule.handler, 'test.home:HomeHandler')
        self.assertEqual(rule_args, {})

    def test_url_match2(self):
        app = get_app()
        environ = get_environ(path='/people/calvin')
        request = get_request(environ)

        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        self.assertEqual(rule.handler, 'test.profile:ProfileHandler')
        self.assertEqual(rule_args, {'username': 'calvin'})

    def test_not_found(self):
        from tipfy import NotFound
        app = get_app()
        environ = get_environ(path='/this-path-is-not-mapped')
        request = get_request(environ)

        app.url_adapter = app.url_map.bind_to_environ(environ)
        self.assertRaises(NotFound, app.url_adapter.match, request.path, return_rule=True)

    def test_url_for(self):
        app = get_app()
        environ = get_environ()
        request = get_request(environ)

        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        from tipfy import url_for
        self.assertEqual(url_for('home'), '/')

    def test_url_for2(self):
        app = get_app()
        environ = get_environ()
        request = get_request(environ)

        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        from tipfy import url_for
        self.assertEqual(url_for('profile', username='calvin'), '/people/calvin')
        self.assertEqual(url_for('profile', username='hobbes'), '/people/hobbes')
        self.assertEqual(url_for('profile', username='moe'), '/people/moe')

    def test_url_for_full(self):
        app = get_app()
        environ = get_environ()
        request = get_request(environ)

        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        from tipfy import url_for
        host = 'http://%s' % environ['HTTP_HOST']
        self.assertEqual(url_for('home', full=True), host + '/')

    def test_url_for_full2(self):
        app = get_app()
        environ = get_environ()
        request = get_request(environ)

        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        from tipfy import url_for
        host = 'http://%s' % environ['HTTP_HOST']
        self.assertEqual(url_for('profile', username='calvin', full=True), host + '/people/calvin')
        self.assertEqual(url_for('profile', username='hobbes', full=True), host + '/people/hobbes')
        self.assertEqual(url_for('profile', username='moe', full=True), host + '/people/moe')

    def test_redirect_to(self):
        from tipfy import local, redirect_to
        app = get_app()
        environ = get_environ()
        request = get_request(environ)
        local.response = get_response()

        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        host = 'http://%s' % environ['HTTP_HOST']

        response = redirect_to('home')
        self.assertEqual(response.headers['location'], host + '/')
        self.assertEqual(response.status_code, 302)

    def test_redirect_to2(self):
        from tipfy import local, redirect_to
        app = get_app()
        environ = get_environ()
        request = get_request(environ)
        local.response = get_response()

        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        host = 'http://%s' % environ['HTTP_HOST']

        response = redirect_to('profile', username='calvin')
        self.assertEqual(response.headers['location'], host + '/people/calvin')
        self.assertEqual(response.status_code, 302)

        response = redirect_to('profile', username='hobbes')
        self.assertEqual(response.headers['location'], host + '/people/hobbes')
        self.assertEqual(response.status_code, 302)

        response = redirect_to('profile', username='moe')
        self.assertEqual(response.headers['location'], host + '/people/moe')
        self.assertEqual(response.status_code, 302)

    def test_redirect_to_301(self):
        from tipfy import local, redirect_to
        app = get_app()
        environ = get_environ()
        request = get_request(environ)
        local.response = get_response()

        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        host = 'http://%s' % environ['HTTP_HOST']

        response = redirect_to('home', code=301)
        self.assertEqual(response.headers['location'], host + '/')
        self.assertEqual(response.status_code, 301)

    def test_redirect_to_invalid_code(self):
        from tipfy import local, redirect_to
        app = get_app()
        environ = get_environ()
        request = get_request(environ)
        local.response = get_response()

        app.url_adapter = app.url_map.bind_to_environ(environ)
        rule, rule_args = app.url_adapter.match(request.path, return_rule=True)

        self.assertRaises(AssertionError, redirect_to, 'home', code=405)


class TestRedirect(unittest.TestCase):
    def test_redirect(self):
        from tipfy import local, redirect
        local.response = get_response()

        response = redirect('http://www.google.com/')
        self.assertEqual(response.headers['location'], 'http://www.google.com/')
        self.assertEqual(response.status_code, 302)

    def test_redirect_301(self):
        from tipfy import local, redirect
        local.response = get_response()

        response = redirect('http://www.google.com/', 301)
        self.assertEqual(response.headers['location'], 'http://www.google.com/')
        self.assertEqual(response.status_code, 301)

    def test_redirect_invalid_code(self):
        from tipfy import local, redirect
        local.response = get_response()

        self.assertRaises(AssertionError, redirect, 'http://www.google.com/', 404)
