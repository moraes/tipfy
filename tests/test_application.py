# -*- coding: utf-8 -*-
"""
    Tests for tipfy.application
"""
import unittest

from nose.tools import assert_raises, raises

from webtest import TestApp

import _base

import tipfy
from tipfy import local, local_manager
from tipfy.application import MiddlewareFactory

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def get_url_map():
    # Fake get_rules() for testing.
    rules = [
        tipfy.Rule('/', endpoint='home', handler='files.app.handlers.HomeHandler'),
    ]

    return tipfy.Map(rules)


def get_app():
    return tipfy.WSGIApplication({
        'tipfy': {
            'url_map': get_url_map(),
            'extensions': ['files.app.extension'],
            'dev': True,
        },
    })


class Handler(tipfy.RequestHandler):
    def get(self, **kwargs):
        return 'handler-get-' + kwargs['some_arg']

    def post(self, **kwargs):
        return 'handler-post-' + kwargs['some_arg']


class TestRequestHandler(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()
        Handler.middleware = []

    def test_dispatch_without_middleware(self):
        handler = Handler()
        assert handler.dispatch('get', some_arg='foo') == 'handler-get-foo'

        handler = Handler()
        assert handler.dispatch('post', some_arg='bar') == 'handler-post-bar'

    @raises(tipfy.MethodNotAllowed)
    def test_dispatch_not_allowed(self):
        handler = Handler()
        handler.dispatch('put', some_arg='test')

    @raises(tipfy.MethodNotAllowed)
    def test_method_not_allowed(self):
        handler = Handler()
        handler.dispatch('foo', some_arg='test')

    #===========================================================================
    # pre_dispatch()
    #===========================================================================
    def test_pre_dispatch_return_response(self):
        app = tipfy.WSGIApplication()
        message = 'I got you.'

        class MiddlewareThatReturns(object):
            def pre_dispatch(self, handler):
                return message

        Handler.middleware = [MiddlewareThatReturns]

        handler = Handler()
        assert handler.dispatch('get', some_arg='foo') == message

        handler = Handler()
        assert handler.dispatch('post', some_arg='bar') == message

    def test_pre_dispatch_set_attribute(self):
        app = tipfy.WSGIApplication()

        class MiddlewareThatSetsAttribute(object):
            def pre_dispatch(self, handler):
                setattr(handler, 'foo', 'bar')

        Handler.middleware = [MiddlewareThatSetsAttribute]

        handler = Handler()

        assert getattr(handler, 'foo', None) == None
        handler.dispatch('get', some_arg='foo')
        assert handler.foo == 'bar'

    #===========================================================================
    # handle_exception()
    #===========================================================================
    @raises(ValueError)
    def test_handle_exception_do_nothing(self):
        app = tipfy.WSGIApplication()
        message = 'I got you.'

        class HandlerThatRaises(tipfy.RequestHandler):
            def get(self, **kwargs):
                raise ValueError()

        class MiddlewareThatReturns(object):
            def handle_exception(self, handler, e):
                pass

        HandlerThatRaises.middleware = [MiddlewareThatReturns]

        handler = HandlerThatRaises()
        assert handler.dispatch('get', some_arg='foo') == message

    @raises(NotImplementedError)
    def test_handle_exception_and_raises(self):
        app = tipfy.WSGIApplication()
        message = 'I got you.'

        class HandlerThatRaises(tipfy.RequestHandler):
            def get(self, **kwargs):
                raise ValueError()

        class MiddlewareThatReturns(object):
            def handle_exception(self, handler, e):
                raise NotImplementedError()

        HandlerThatRaises.middleware = [MiddlewareThatReturns]

        handler = HandlerThatRaises()
        assert handler.dispatch('get', some_arg='foo') == message

    def test_handle_exception_return_response(self):
        app = tipfy.WSGIApplication()
        message = 'I got you.'

        class HandlerThatRaises(tipfy.RequestHandler):
            def get(self, **kwargs):
                raise ValueError()

        class MiddlewareThatReturns(object):
            def handle_exception(self, handler, e):
                return message

        HandlerThatRaises.middleware = [MiddlewareThatReturns]

        handler = HandlerThatRaises()
        assert handler.dispatch('get', some_arg='foo') == message

    #===========================================================================
    # post_dispatch()
    #===========================================================================
    def test_post_dispatch_return_response(self):
        app = tipfy.WSGIApplication()
        message = 'I got you.'

        class MiddlewareThatReturns(object):
            def post_dispatch(self, handler, response):
                return message

        Handler.middleware = [MiddlewareThatReturns]

        handler = Handler()
        assert handler.dispatch('get', some_arg='foo') == message

        handler = Handler()
        assert handler.dispatch('post', some_arg='bar') == message

    def test_post_dispatch_set_attribute(self):
        app = tipfy.WSGIApplication()

        class MiddlewareThatSetsAttribute(object):
            def post_dispatch(self, handler, response):
                setattr(handler, 'foo', 'bar')
                return response

        Handler.middleware = [MiddlewareThatSetsAttribute]

        handler = Handler()

        assert getattr(handler, 'foo', None) == None
        handler.dispatch('get', some_arg='foo')
        assert handler.foo == 'bar'


class TestMiddlewareFactory(unittest.TestCase):
    def tearDown(self):
        local_manager.cleanup()

    def test_get_instance_methods(self):
        from tipfy.ext import session

        factory = MiddlewareFactory()
        res = factory.get_instance_methods(session.SessionMiddleware)
        assert len(res) == 3

        assert 'tipfy.ext.session.SessionMiddleware' in factory.instances
        instance = factory.instances['tipfy.ext.session.SessionMiddleware']
        assert isinstance(instance, session.SessionMiddleware)

        assert 'tipfy.ext.session.SessionMiddleware' in factory.instance_methods
        assert res[0] == getattr(instance, 'pre_dispatch')
        assert res[1] is None
        assert res[2] == getattr(instance, 'post_dispatch')

    def test_get_instance_methods_using_string(self):
        from tipfy.ext import session

        factory = MiddlewareFactory()
        res = factory.get_instance_methods('tipfy.ext.session.SessionMiddleware')
        assert len(res) == 3

        assert 'tipfy.ext.session.SessionMiddleware' in factory.instances
        instance = factory.instances['tipfy.ext.session.SessionMiddleware']
        assert isinstance(instance, session.SessionMiddleware)

        assert 'tipfy.ext.session.SessionMiddleware' in factory.instance_methods
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

        assert 'tipfy.ext.session.SessionMiddleware' in factory.instances
        assert 'tipfy.ext.i18n.I18nMiddleware' in factory.instances
        instance_1 = factory.instances['tipfy.ext.session.SessionMiddleware']
        instance_2 = factory.instances['tipfy.ext.i18n.I18nMiddleware']
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

        assert 'tipfy.ext.session.SessionMiddleware' in factory.instances
        assert 'tipfy.ext.i18n.I18nMiddleware' in factory.instances
        instance_1 = factory.instances['tipfy.ext.session.SessionMiddleware']
        instance_2 = factory.instances['tipfy.ext.i18n.I18nMiddleware']
        assert isinstance(instance_1, session.SessionMiddleware)
        assert isinstance(instance_2, i18n.I18nMiddleware)

        assert res['pre_dispatch'][0] == getattr(instance_1, 'pre_dispatch')
        # post_dispatch is reversed
        assert res['post_dispatch'][0] == getattr(instance_2, 'post_dispatch')
        assert res['post_dispatch'][1] == getattr(instance_1, 'post_dispatch')



class TestWSGIApplication(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()


class TestMiscelaneous(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_make_wsgi_app(self):
        app = tipfy.make_wsgi_app({'tipfy': {
            'extensions': ['files.app.extension'],
        }})

        assert isinstance(app, tipfy.WSGIApplication)

    def test_make_wsgi_app2(self):
        app = tipfy.make_wsgi_app({'tipfy': {
            'foo': 'bar'
        }})

        assert isinstance(app, tipfy.WSGIApplication)
        assert app.config.get('tipfy', 'foo') == 'bar'

    def test_run_wsgi_app(self):
        """We aren't testing anything here."""
        app = TestApp(get_app())
        response = app.get('/')
        assert 'Hello, World!' in str(response)

    def test_ultimate_sys_path(self):
        """Mostly here to not be marked as uncovered."""
        from tipfy.application import _ULTIMATE_SYS_PATH, fix_sys_path
        fix_sys_path()

    def test_ultimate_sys_path2(self):
        """Mostly here to not be marked as uncovered."""
        from tipfy.application import _ULTIMATE_SYS_PATH, fix_sys_path
        _ULTIMATE_SYS_PATH = []
        fix_sys_path()
