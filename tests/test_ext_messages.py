# -*- coding: utf-8 -*-
"""
    Tests for tipfy.EventHandler and tipfy.EventManager.
"""
import unittest
import sys
from _base import get_app, get_environ, get_request, get_response


from werkzeug import Request
from tipfy import local
from tipfy.ext.messages import Messages, set_messages, set_flash, get_flash


class TestRequest(Request):
    @property
    def cookies(self):
        """The retrieved cookie values as regular dictionary."""
        return parse_cookie(self.environ, self.charset,
                            cls=ImmutableTypeConversionDict)


def get_app_environ_request_response(**kwargs):
    app = get_app({
        'tipfy': {
            'hooks': {
                'pos_init_app': ['tipfy.ext.i18n:set_app_hooks'],
                # ...
            },
        },
    })
    environ = get_environ(**kwargs)
    request = get_request(environ)
    response = get_response()
    return app, environ, request, response


class TestMessages(unittest.TestCase):
    def test_set_messages(self):
        app, environ, request, response = get_app_environ_request_response()
        local.request = request

        set_messages(request, app)
        self.assertEqual(isinstance(local.messages, Messages), True)

    def test_messages_init(self):
        pass

    def test_messages_len(self):
        app, environ, request, response = get_app_environ_request_response()
        local.request = request

        messages = Messages()
        self.assertEqual(len(messages), 0)
        messages.add('error', 'foo', 'bar')
        self.assertEqual(len(messages), 1)
        messages.add_form_error('baz', 'ding')
        self.assertEqual(len(messages), 2)
        messages.set_flash('baz', 'ding', 'weee')
        self.assertEqual(len(messages), 2)

    def test_messages_str(self):
        app, environ, request, response = get_app_environ_request_response()
        local.request = request

        messages = Messages()
        self.assertEqual(str(messages), '')
        messages.add('error', 'foo', 'bar')
        self.assertEqual(str(messages), "[('body', 'foo'), ('level', 'error'), ('life', 5000), ('title', 'bar')]")
        messages.add_form_error('baz', 'ding')
        self.assertEqual(str(messages), "[('body', 'foo'), ('level', 'error'), ('life', 5000), ('title', 'bar')]\n[('body', 'baz'), ('level', 'error'), ('life', None), ('title', 'ding')]")
        messages.set_flash('baz', 'ding', 'weee')
        self.assertEqual(str(messages), "[('body', 'foo'), ('level', 'error'), ('life', 5000), ('title', 'bar')]\n[('body', 'baz'), ('level', 'error'), ('life', None), ('title', 'ding')]")

    def test_messages_add(self):
        pass

    def test_messages_add_form_error(self):
        app, environ, request, response = get_app_environ_request_response()
        local.request = request

        app.hooks.call('pre_dispatch_handler', request=local.request, app=app)

        messages = Messages()
        self.assertEqual(str(messages), '')

        messages.add_form_error('foo', 'bar')
        self.assertEqual(str(messages), "[('body', 'foo'), ('level', 'error'), ('life', None), ('title', 'bar')]")

        messages.add_form_error('baz')
        self.assertEqual(str(messages), "[('body', 'foo'), ('level', 'error'), ('life', None), ('title', 'bar')]\n[('body', 'baz'), ('level', 'error'), ('life', None), ('title', u'Error')]")

    def test_messages_set_flash(self):
        pass

    def test_get_flash(self):
        pass

    def test_set_flash(self):
        pass
