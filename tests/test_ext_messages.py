# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.messages.
"""
import unittest
from base64 import b64encode, b64decode

from django.utils import simplejson

import tipfy
from tipfy import local, local_manager
from tipfy.ext import messages


# Some dummy values for cookies.
value_1 = b64encode(simplejson.dumps({'foo': 'baz'}))
value_2 = b64encode(simplejson.dumps({'bar': 'ding'}))


class Request(object):
    """A fake request object with cookies."""
    def __init__(self, cookies=None):
        self.cookies = cookies or {}


class Response(object):
    """A fake response object with cookies."""
    def __init__(self):
        self.cookies_to_set = []
        self.cookies_to_delete = []

    def set_cookie(self, key, value):
        self.cookies_to_set.append((key, value))

    def delete_cookie(self, key):
        self.cookies_to_delete.append(key)


class TestMessages(unittest.TestCase):
    def tearDown(self):
        local_manager.cleanup()

    def test_get_flash(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request(cookies={'tipfy.flash': value_1})

        assert messages.get_flash() == {'foo': 'baz'}
        assert local.ext_messages_delete == ['tipfy.flash']

        assert messages.get_flash('tipfy.flash') == {'foo': 'baz'}
        assert local.ext_messages_delete == ['tipfy.flash']

    def test_get_flash_with_custom_key(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request(cookies={'foo': value_1, 'bar': value_2})

        assert messages.get_flash('foo') == {'foo': 'baz'}
        assert local.ext_messages_delete == ['foo']

        assert messages.get_flash('bar') == {'bar': 'ding'}
        assert local.ext_messages_delete == ['foo', 'bar']

    def test_get_flash_with_configured_key(self):
        local.app = tipfy.WSGIApplication({'tipfy.ext.messages': {'cookie_name': 'my_flash'}})
        local.request = Request(cookies={'my_flash': value_1})

        assert messages.get_flash() == {'foo': 'baz'}
        assert local.ext_messages_delete == ['my_flash']

        assert messages.get_flash('my_flash') == {'foo': 'baz'}
        assert local.ext_messages_delete == ['my_flash']

    def test_set_flash(self):
        local.app = tipfy.WSGIApplication()
        assert getattr(local, 'ext_messages_set', None) is None

        messages.set_flash({'foo': 'baz'})
        assert local.ext_messages_set == [
            ('tipfy.flash', {'foo': 'baz'}),
        ]

    def test_set_flash_with_custom_key(self):
        local.app = tipfy.WSGIApplication()
        assert getattr(local, 'ext_messages_set', None) is None

        messages.set_flash({'foo': 'baz'}, 'foo')
        assert local.ext_messages_set == [
            ('foo', {'foo': 'baz'}),
        ]

        messages.set_flash({'bar': 'ding'}, 'bar')
        assert local.ext_messages_set == [
            ('foo', {'foo': 'baz'}),
            ('bar', {'bar': 'ding'}),
        ]

    def test_set_flash_with_configured_key(self):
        local.app = tipfy.WSGIApplication({'tipfy.ext.messages': {'cookie_name': 'my_flash'}})
        assert getattr(local, 'ext_messages_set', None) is None

        messages.set_flash({'foo': 'baz'})
        assert local.ext_messages_set == [
            ('my_flash', {'foo': 'baz'}),
        ]

    def test_flash_middleware(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request(cookies={'my_flash': value_1})
        response = Response()

        middleware = messages.FlashMiddleware()
        response = middleware.post_dispatch(None, response)

        assert getattr(local, 'ext_messages_set', None) is None
        assert response.cookies_to_set == []
        assert response.cookies_to_delete == []

        # Add one, remove one.
        messages.set_flash({'bar': 'ding'}, 'bar')
        assert messages.get_flash('my_flash') == {'foo': 'baz'}

        response = middleware.post_dispatch(None, response)

        assert response.cookies_to_set == [('bar', value_2)]
        assert response.cookies_to_delete == ['my_flash']

    def test_flash_middleware_set_same_key_twice(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request()
        response = Response()

        middleware = messages.FlashMiddleware()
        response = middleware.post_dispatch(None, response)

        assert response.cookies_to_set == []
        assert response.cookies_to_delete == []

        # value_1 won't be set
        messages.set_flash({'foo': 'baz'}, 'my_flash')
        # value_2 will be set (reversal order)
        messages.set_flash({'bar': 'ding'}, 'my_flash')

        response = middleware.post_dispatch(None, response)

        assert response.cookies_to_set == [('my_flash', value_2)]
        assert response.cookies_to_delete == []

    def test_flash_middleware_set_and_delete(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request(cookies={'my_flash': value_1})
        response = Response()

        middleware = messages.FlashMiddleware()
        response = middleware.post_dispatch(None, response)

        assert response.cookies_to_set == []
        assert response.cookies_to_delete == []

        # Add one, remove one.
        messages.set_flash({'bar': 'ding'}, 'my_flash')
        assert messages.get_flash('my_flash') == {'foo': 'baz'}

        response = middleware.post_dispatch(None, response)

        assert response.cookies_to_set == [('my_flash', value_2)]
        assert response.cookies_to_delete == []

    def test_messages_mixin(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request()
        mixin = messages.MessagesMixin()
        assert mixin.messages == []

    def test_messages_mixin_with_flash(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request(cookies={'tipfy.flash': value_1})
        mixin = messages.MessagesMixin()
        assert mixin.messages == [{'foo': 'baz'}]

    def test_messages_mixin_set_message(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request(cookies={'tipfy.flash': value_1})

        mixin = messages.MessagesMixin()
        mixin.set_message('success', 'Hello, world!', title='HAI', life=5000, flash=False)

        assert mixin.messages == [{'foo': 'baz'}, {'level': 'success', 'title': 'HAI', 'body': 'Hello, world!', 'life': 5000}]

    def test_messages_mixin_set_flash_message(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request(cookies={'tipfy.flash': value_1})

        assert getattr(local, 'ext_messages_set', None) is None

        mixin = messages.MessagesMixin()
        mixin.set_message('success', 'Hello, world!', title='HAI', life=5000, flash=True)

        assert mixin.messages == [{'foo': 'baz'}]
        assert local.ext_messages_set == [
            ('tipfy.flash', {'level': 'success', 'title': 'HAI', 'body': 'Hello, world!', 'life': 5000}),
        ]

    def test_messages_mixin_get_flash(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request(cookies={'tipfy.flash': value_1})

        mixin = messages.MessagesMixin()
        assert mixin.get_flash() == {'foo': 'baz'}
        assert mixin.get_flash('tipfy.flash') == {'foo': 'baz'}

    def test_messages_mixin_get_flash_with_custom_key(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request(cookies={'foo': value_1, 'bar': value_2})

        mixin = messages.MessagesMixin()
        assert mixin.get_flash('foo') == {'foo': 'baz'}
        assert mixin.get_flash('bar') == {'bar': 'ding'}

    def test_messages_mixin_set_flash(self):
        local.app = tipfy.WSGIApplication()
        assert getattr(local, 'ext_messages_set', None) is None

        mixin = messages.MessagesMixin()
        mixin.set_flash({'foo': 'baz'})
        assert local.ext_messages_set == [
            ('tipfy.flash', {'foo': 'baz'}),
        ]

    def test_messages_mixin_set_flash_with_custom_key(self):
        local.app = tipfy.WSGIApplication()
        assert getattr(local, 'ext_messages_set', None) is None

        mixin = messages.MessagesMixin()
        mixin.set_flash({'foo': 'baz'}, 'foo')
        assert local.ext_messages_set == [
            ('foo', {'foo': 'baz'}),
        ]

        mixin.set_flash({'bar': 'ding'}, 'bar')
        assert local.ext_messages_set == [
            ('foo', {'foo': 'baz'}),
            ('bar', {'bar': 'ding'}),
        ]

    def test_messages_mixin_set_form_error(self):
        local.app = tipfy.WSGIApplication()
        local.request = Request(cookies={'tipfy.flash': value_1})

        mixin = messages.MessagesMixin()
        mixin.set_form_error('Hello, world!', title='HAI')

        assert mixin.messages == [{'foo': 'baz'}, {'level': 'error', 'title': 'HAI', 'body': 'Hello, world!', 'life': None}]
