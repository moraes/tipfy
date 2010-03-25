# -*- coding: utf-8 -*-
"""
    Tests for tipfy.application
"""
import unittest

from nose.tools import assert_raises, raises

import _base

import tipfy
from tipfy import local, local_manager
from tipfy.application import MiddlewareFactory

RESPONSE = 'Hello, World!'

class MyHandler(tipfy.RequestHandler):
    def get(self, **kwargs):
        return RESPONSE

class TestRequestHandler(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()
        MyHandler.middleware = []

    @raises(tipfy.MethodNotAllowed)
    def test_method_not_allowed(self):
        handler = MyHandler()
        handler.dispatch('foo')

    def test_dispatch_without_middleware(self):
        handler = MyHandler()
        assert handler.dispatch('get') == RESPONSE


class TestMiddlewareFactory(unittest.TestCase):
    def tearDown(self):
        local_manager.cleanup()

    def test_get_methods(self):
        from tipfy.ext import session

        factory = MiddlewareFactory()
        res = factory.get_methods(session.SessionMiddleware)
        assert len(res) == 3

        assert 'tipfy.ext.session.SessionMiddleware' in factory.middleware
        instance = factory.middleware['tipfy.ext.session.SessionMiddleware']
        assert isinstance(instance, session.SessionMiddleware)

        assert 'tipfy.ext.session.SessionMiddleware' in factory.middleware_methods
        assert res[0] == getattr(instance, 'pre_dispatch')
        assert res[1] is None
        assert res[2] == getattr(instance, 'post_dispatch')

    def test_get_methods_using_string(self):
        from tipfy.ext import session

        factory = MiddlewareFactory()
        res = factory.get_methods('tipfy.ext.session.SessionMiddleware')
        assert len(res) == 3

        assert 'tipfy.ext.session.SessionMiddleware' in factory.middleware
        instance = factory.middleware['tipfy.ext.session.SessionMiddleware']
        assert isinstance(instance, session.SessionMiddleware)

        assert 'tipfy.ext.session.SessionMiddleware' in factory.middleware_methods
        assert res[0] == getattr(instance, 'pre_dispatch')
        assert res[1] is None
        assert res[2] == getattr(instance, 'post_dispatch')

    def test_get_handler_middleware(self):
        from tipfy.ext import session
        from tipfy.ext import i18n

        class MyHandler(object):
            middleware = [session.SessionMiddleware, i18n.I18nMiddleware]

        factory = MiddlewareFactory()
        handler = MyHandler()
        res = factory.get_handler_middleware(handler)
        assert len(res) == 3

        assert 'pre_dispatch' in res
        assert 'handle_exception' in res
        assert 'post_dispatch' in res

        assert len(res['pre_dispatch']) == 1
        assert len(res['handle_exception']) == 0
        assert len(res['post_dispatch']) == 2

        assert 'tipfy.ext.session.SessionMiddleware' in factory.middleware
        assert 'tipfy.ext.i18n.I18nMiddleware' in factory.middleware
        instance_1 = factory.middleware['tipfy.ext.session.SessionMiddleware']
        instance_2 = factory.middleware['tipfy.ext.i18n.I18nMiddleware']
        assert isinstance(instance_1, session.SessionMiddleware)
        assert isinstance(instance_2, i18n.I18nMiddleware)

        assert res['pre_dispatch'][0] == getattr(instance_1, 'pre_dispatch')
        # post_dispatch is reversed
        assert res['post_dispatch'][0] == getattr(instance_2, 'post_dispatch')
        assert res['post_dispatch'][1] == getattr(instance_1, 'post_dispatch')

    def test_get_handler_middleware_using_string(self):
        from tipfy.ext import session
        from tipfy.ext import i18n

        class MyHandler(object):
            middleware = ['tipfy.ext.session.SessionMiddleware', 'tipfy.ext.i18n.I18nMiddleware']

        factory = MiddlewareFactory()
        handler = MyHandler()
        res = factory.get_handler_middleware(handler)
        assert len(res) == 3

        assert 'pre_dispatch' in res
        assert 'handle_exception' in res
        assert 'post_dispatch' in res

        assert len(res['pre_dispatch']) == 1
        assert len(res['handle_exception']) == 0
        assert len(res['post_dispatch']) == 2

        assert 'tipfy.ext.session.SessionMiddleware' in factory.middleware
        assert 'tipfy.ext.i18n.I18nMiddleware' in factory.middleware
        instance_1 = factory.middleware['tipfy.ext.session.SessionMiddleware']
        instance_2 = factory.middleware['tipfy.ext.i18n.I18nMiddleware']
        assert isinstance(instance_1, session.SessionMiddleware)
        assert isinstance(instance_2, i18n.I18nMiddleware)

        assert res['pre_dispatch'][0] == getattr(instance_1, 'pre_dispatch')
        # post_dispatch is reversed
        assert res['post_dispatch'][0] == getattr(instance_2, 'post_dispatch')
        assert res['post_dispatch'][1] == getattr(instance_1, 'post_dispatch')

