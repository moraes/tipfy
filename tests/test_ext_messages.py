# -*- coding: utf-8 -*-
"""
    Tests for tipfy.EventHandler and tipfy.EventManager.
"""
import unittest
import pickle
from base64 import b64encode, b64decode
from django.utils import simplejson

from werkzeug import Request, Response
from werkzeug.test import Client

from _base import get_app, get_environ, get_request, get_response
from tipfy import local, request, response, Rule, RequestHandler
from tipfy.ext.messages import Messages, set_messages, set_flash, get_flash


class SetFlashHandler_1(RequestHandler):
    def get(self, **kwargs):
        if request.args.get('set-messages-flash', None) == '1':
            local.messages.set_flash('error', 'An error occurred.')
        elif request.args.get('set-flash', None) == '1':
            set_flash({'foo': 'bar'})

        response.data = str(local.messages)
        return response


def get_rules():
    return [Rule('/', endpoint='home', handler='%s:SetFlashHandler_1' % __name__)]


def get_app_environ_request_response(**kwargs):
    app = get_app({
        'tipfy': {
            'hooks': {
                'pos_init_app': ['tipfy.ext.i18n:set_app_hooks'],
                'pre_dispatch_handler': ['tipfy.ext.messages:set_messages'],
            },
            'urls': '%s:get_rules' % __name__
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
        assert isinstance(local.messages, Messages) is True

    def test_messages_init(self):
        pass

    def test_messages_len(self):
        app, environ, request, response = get_app_environ_request_response()
        local.request = request

        messages = Messages()
        assert len(messages) == 0

        messages.add('error', 'foo', 'bar')
        assert len(messages) == 1

        messages.add_form_error('baz', 'ding')
        assert len(messages) == 2

        messages.set_flash('baz', 'ding', 'weee')
        assert len(messages) == 2

    def test_messages_str(self):
        app, environ, request, response = get_app_environ_request_response()
        local.request = request

        messages = Messages()
        assert str(messages) == ''

        messages.add('error', 'foo', 'bar')
        assert str(messages) == "[('body', 'foo'), ('level', 'error'), ('life', 5000), ('title', 'bar')]"

        messages.add_form_error('baz', 'ding')
        assert str(messages) == "[('body', 'foo'), ('level', 'error'), ('life', 5000), ('title', 'bar')]\n[('body', 'baz'), ('level', 'error'), ('life', None), ('title', 'ding')]"

        messages.set_flash('baz', 'ding', 'weee')
        assert str(messages) == "[('body', 'foo'), ('level', 'error'), ('life', 5000), ('title', 'bar')]\n[('body', 'baz'), ('level', 'error'), ('life', None), ('title', 'ding')]"

    def test_messages_add(self):
        pass

    def test_messages_add_form_error(self):
        app, environ, request, response = get_app_environ_request_response()
        local.request = request

        app.hooks.call('pre_dispatch_handler', request=local.request, app=app)

        messages = Messages()
        assert str(messages) == ''

        messages.add_form_error('foo', 'bar')
        assert str(messages) == "[('body', 'foo'), ('level', 'error'), ('life', None), ('title', 'bar')]"

        messages.add_form_error('baz')
        assert str(messages) == "[('body', 'foo'), ('level', 'error'), ('life', None), ('title', 'bar')]\n[('body', 'baz'), ('level', 'error'), ('life', None), ('title', u'Error')]"

        messages = Messages()
        messages.add_form_error()
        assert str(messages) == "[('body', u'A problem occurred. Please correct the errors listed in the form.'), ('level', 'error'), ('life', None), ('title', u'Error')]"

    def test_messages_set_flash(self):
        app, environ, request, response = get_app_environ_request_response()
        client = Client(app, Response)

        response = client.get('/?set-messages-flash=1')

        # next request must have a flash set.
        response = client.get('/')
        res = response.data
        assert res == "[(u'body', u'An error occurred.'), (u'level', u'error'), (u'life', 5000), (u'title', None)]"

    def test_get_flash(self):
        pass

    def test_set_flash(self):
        local.response = Response()
        data = {'foo': 'bar'}
        set_flash(data)

        res = local.response.headers.to_list()
        expected = [('Content-Type', 'text/plain; charset=utf-8'),
                    ('Set-Cookie', 'tipfy.flash="%s"; Path=/' % b64encode(simplejson.dumps(data)))]

        assert res == expected
