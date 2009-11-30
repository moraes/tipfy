# -*- coding: utf-8 -*-
"""
    Tests for tipfy
"""
import unittest
from nose.tools import raises

from _base import get_app, get_environ, get_request, get_response
from tipfy import local, render_json_response, Response, RequestHandler, \
    MethodNotAllowed

class Handler1(RequestHandler):
    def get(self, **kwargs):
        return 'handler1-get-' + kwargs['some_arg']

    def post(self, **kwargs):
        return 'handler1-post-' + kwargs['some_arg']


class TestRequestHandler(unittest.TestCase):
    def test_dispatch(self):
        handler = Handler1()
        assert handler.dispatch('get', some_arg='test') == 'handler1-get-test'

        handler = Handler1()
        assert handler.dispatch('post', some_arg='test') == 'handler1-post-test'

    @raises(MethodNotAllowed)
    def test_dispatch_not_allowed(self):
        handler = Handler1()
        handler.dispatch('put', some_arg='test')


class TestMiscelaneous(unittest.TestCase):
    def test_render_json_response(self):
        local.response = get_response()
        response = render_json_response({'foo': 'bar'})

        assert isinstance(response, Response)
        assert response.mimetype == 'application/json'
        assert response.data == '{"foo": "bar"}'
