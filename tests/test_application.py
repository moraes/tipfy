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
from tipfy.application import MiddlewareFactory, set_extensions_compatibility

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
            'dev': True,
        },
    })


class Handler(tipfy.RequestHandler):
    def get(self, **kwargs):
        return 'handler-get-' + kwargs['some_arg']

    def post(self, **kwargs):
        return 'handler-post-' + kwargs['some_arg']


class SomeObject(object):
    pass


class Middleware_1(object):
    def post_make_app(self, app):
        pass

    def pre_run_app(self, app):
        pass

    def post_run_app(self, response):
        pass

    def pre_dispatch(self):
        pass

    def post_dispatch(self, response):
        pass

    def handle_exception(self, e, handler=None):
        pass


class Middleware_2(object):
    def post_make_app(self, app):
        pass

    def pre_run_app(self, app):
        pass


class Middleware_3(object):
    def post_run_app(self, response):
        pass

    def post_dispatch(self, response):
        pass

    def handle_exception(self, e, handler=None):
        pass


class Middleware_4(object):
    def post_run_app(self, response):
        pass

    def post_dispatch(self, response):
        pass

    def handle_exception(self, e, handler=None):
        pass


class Middleware_5(object):
    def post_run_app(self, response):
        pass

    def post_dispatch(self, response):
        pass

    def handle_exception(self, e, handler=None):
        pass


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
            def handle_exception(self, e, handler=None):
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
            def handle_exception(self, e, handler=None):
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
            def handle_exception(self, e, handler=None):
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

    def test_get_middleware(self):
        factory = MiddlewareFactory()
        obj = SomeObject()
        middleware = factory.get_middleware(obj, [Middleware_1, Middleware_2])

        assert len(factory.obj_middleware) == 1
        assert len(factory.instances) == 2
        assert len(factory.methods) == 2

        assert 'test_application.SomeObject' in factory.obj_middleware

        assert 'test_application.Middleware_1' in factory.instances
        assert 'test_application.Middleware_2' in factory.instances

        assert 'test_application.Middleware_1' in factory.methods
        assert 'test_application.Middleware_2' in factory.methods

        assert 'post_make_app' in middleware
        assert 'pre_run_app' in middleware
        assert 'post_run_app' in middleware
        assert 'pre_dispatch' in middleware
        assert 'post_dispatch' in middleware
        assert 'handle_exception' in middleware

        assert len(middleware['post_make_app']) == 2
        assert len(middleware['pre_run_app']) == 2
        assert len(middleware['post_run_app']) == 1
        assert len(middleware['pre_dispatch']) == 1
        assert len(middleware['post_dispatch']) == 1
        assert len(middleware['handle_exception']) == 1

        assert middleware['post_make_app'][0] == factory.instances['test_application.Middleware_1'].post_make_app
        assert middleware['post_make_app'][1] == factory.instances['test_application.Middleware_2'].post_make_app
        assert middleware['pre_run_app'][0] == factory.instances['test_application.Middleware_1'].pre_run_app
        assert middleware['pre_run_app'][1] == factory.instances['test_application.Middleware_2'].pre_run_app
        assert middleware['post_run_app'][0] == factory.instances['test_application.Middleware_1'].post_run_app
        assert middleware['pre_dispatch'][0] == factory.instances['test_application.Middleware_1'].pre_dispatch
        assert middleware['post_dispatch'][0] == factory.instances['test_application.Middleware_1'].post_dispatch
        assert middleware['handle_exception'][0] == factory.instances['test_application.Middleware_1'].handle_exception

        assert len(factory.obj_middleware['test_application.SomeObject']['post_make_app']) == 2
        assert len(factory.obj_middleware['test_application.SomeObject']['pre_run_app']) == 2
        assert len(factory.obj_middleware['test_application.SomeObject']['post_run_app']) == 1
        assert len(factory.obj_middleware['test_application.SomeObject']['pre_dispatch']) == 1
        assert len(factory.obj_middleware['test_application.SomeObject']['post_dispatch']) == 1
        assert len(factory.obj_middleware['test_application.SomeObject']['handle_exception']) == 1

        assert factory.obj_middleware['test_application.SomeObject']['post_make_app'][0] == factory.instances['test_application.Middleware_1'].post_make_app
        assert factory.obj_middleware['test_application.SomeObject']['post_make_app'][1] == factory.instances['test_application.Middleware_2'].post_make_app
        assert factory.obj_middleware['test_application.SomeObject']['pre_run_app'][0] == factory.instances['test_application.Middleware_1'].pre_run_app
        assert factory.obj_middleware['test_application.SomeObject']['pre_run_app'][1] == factory.instances['test_application.Middleware_2'].pre_run_app
        assert factory.obj_middleware['test_application.SomeObject']['post_run_app'][0] == factory.instances['test_application.Middleware_1'].post_run_app
        assert factory.obj_middleware['test_application.SomeObject']['pre_dispatch'][0] == factory.instances['test_application.Middleware_1'].pre_dispatch
        assert factory.obj_middleware['test_application.SomeObject']['post_dispatch'][0] == factory.instances['test_application.Middleware_1'].post_dispatch
        assert factory.obj_middleware['test_application.SomeObject']['handle_exception'][0] == factory.instances['test_application.Middleware_1'].handle_exception

    def test_load_middleware(self):
        factory = MiddlewareFactory()
        middleware = factory.load_middleware([Middleware_1, Middleware_2])
        middleware_2 = factory.load_middleware([Middleware_1, Middleware_2])

        assert len(factory.instances) == 2
        assert len(factory.methods) == 2

        assert 'test_application.Middleware_1' in factory.instances
        assert 'test_application.Middleware_2' in factory.instances

        assert 'test_application.Middleware_1' in factory.methods
        assert 'test_application.Middleware_2' in factory.methods

        assert 'post_make_app' in middleware
        assert 'pre_run_app' in middleware
        assert 'post_run_app' in middleware
        assert 'pre_dispatch' in middleware
        assert 'post_dispatch' in middleware
        assert 'handle_exception' in middleware

        assert len(middleware['post_make_app']) == 2
        assert len(middleware['pre_run_app']) == 2
        assert len(middleware['post_run_app']) == 1
        assert len(middleware['pre_dispatch']) == 1
        assert len(middleware['post_dispatch']) == 1
        assert len(middleware['handle_exception']) == 1

        assert middleware['post_make_app'][0] == factory.instances['test_application.Middleware_1'].post_make_app
        assert middleware['post_make_app'][1] == factory.instances['test_application.Middleware_2'].post_make_app
        assert middleware['pre_run_app'][0] == factory.instances['test_application.Middleware_1'].pre_run_app
        assert middleware['pre_run_app'][1] == factory.instances['test_application.Middleware_2'].pre_run_app
        assert middleware['post_run_app'][0] == factory.instances['test_application.Middleware_1'].post_run_app
        assert middleware['pre_dispatch'][0] == factory.instances['test_application.Middleware_1'].pre_dispatch
        assert middleware['post_dispatch'][0] == factory.instances['test_application.Middleware_1'].post_dispatch
        assert middleware['handle_exception'][0] == factory.instances['test_application.Middleware_1'].handle_exception

        assert 'post_make_app' in middleware_2
        assert 'pre_run_app' in middleware_2
        assert 'post_run_app' in middleware_2
        assert 'pre_dispatch' in middleware_2
        assert 'post_dispatch' in middleware_2
        assert 'handle_exception' in middleware_2

        assert len(middleware_2['post_make_app']) == 2
        assert len(middleware_2['pre_run_app']) == 2
        assert len(middleware_2['post_run_app']) == 1
        assert len(middleware_2['pre_dispatch']) == 1
        assert len(middleware_2['post_dispatch']) == 1
        assert len(middleware_2['handle_exception']) == 1

        assert middleware_2['post_make_app'][0] == factory.instances['test_application.Middleware_1'].post_make_app
        assert middleware_2['post_make_app'][1] == factory.instances['test_application.Middleware_2'].post_make_app
        assert middleware_2['pre_run_app'][0] == factory.instances['test_application.Middleware_1'].pre_run_app
        assert middleware_2['pre_run_app'][1] == factory.instances['test_application.Middleware_2'].pre_run_app
        assert middleware_2['post_run_app'][0] == factory.instances['test_application.Middleware_1'].post_run_app
        assert middleware_2['pre_dispatch'][0] == factory.instances['test_application.Middleware_1'].pre_dispatch
        assert middleware_2['post_dispatch'][0] == factory.instances['test_application.Middleware_1'].post_dispatch
        assert middleware_2['handle_exception'][0] == factory.instances['test_application.Middleware_1'].handle_exception

    def test_load_middleware_using_strings(self):
        factory = MiddlewareFactory()
        middleware = factory.load_middleware(['test_application.Middleware_1', 'test_application.Middleware_2'])
        middleware_2 = factory.load_middleware(['test_application.Middleware_1', 'test_application.Middleware_2'])

        assert len(factory.instances) == 2
        assert len(factory.methods) == 2

        assert 'test_application.Middleware_1' in factory.instances
        assert 'test_application.Middleware_2' in factory.instances

        assert 'test_application.Middleware_1' in factory.methods
        assert 'test_application.Middleware_2' in factory.methods

        assert 'post_make_app' in middleware
        assert 'pre_run_app' in middleware
        assert 'post_run_app' in middleware
        assert 'pre_dispatch' in middleware
        assert 'post_dispatch' in middleware
        assert 'handle_exception' in middleware

        assert len(middleware['post_make_app']) == 2
        assert len(middleware['pre_run_app']) == 2
        assert len(middleware['post_run_app']) == 1
        assert len(middleware['pre_dispatch']) == 1
        assert len(middleware['post_dispatch']) == 1
        assert len(middleware['handle_exception']) == 1

        assert middleware['post_make_app'][0] == factory.instances['test_application.Middleware_1'].post_make_app
        assert middleware['post_make_app'][1] == factory.instances['test_application.Middleware_2'].post_make_app
        assert middleware['pre_run_app'][0] == factory.instances['test_application.Middleware_1'].pre_run_app
        assert middleware['pre_run_app'][1] == factory.instances['test_application.Middleware_2'].pre_run_app
        assert middleware['post_run_app'][0] == factory.instances['test_application.Middleware_1'].post_run_app
        assert middleware['pre_dispatch'][0] == factory.instances['test_application.Middleware_1'].pre_dispatch
        assert middleware['post_dispatch'][0] == factory.instances['test_application.Middleware_1'].post_dispatch
        assert middleware['handle_exception'][0] == factory.instances['test_application.Middleware_1'].handle_exception

        assert 'post_make_app' in middleware_2
        assert 'pre_run_app' in middleware_2
        assert 'post_run_app' in middleware_2
        assert 'pre_dispatch' in middleware_2
        assert 'post_dispatch' in middleware_2
        assert 'handle_exception' in middleware_2

        assert len(middleware_2['post_make_app']) == 2
        assert len(middleware_2['pre_run_app']) == 2
        assert len(middleware_2['post_run_app']) == 1
        assert len(middleware_2['pre_dispatch']) == 1
        assert len(middleware_2['post_dispatch']) == 1
        assert len(middleware_2['handle_exception']) == 1

        assert middleware_2['post_make_app'][0] == factory.instances['test_application.Middleware_1'].post_make_app
        assert middleware_2['post_make_app'][1] == factory.instances['test_application.Middleware_2'].post_make_app
        assert middleware_2['pre_run_app'][0] == factory.instances['test_application.Middleware_1'].pre_run_app
        assert middleware_2['pre_run_app'][1] == factory.instances['test_application.Middleware_2'].pre_run_app
        assert middleware_2['post_run_app'][0] == factory.instances['test_application.Middleware_1'].post_run_app
        assert middleware_2['pre_dispatch'][0] == factory.instances['test_application.Middleware_1'].pre_dispatch
        assert middleware_2['post_dispatch'][0] == factory.instances['test_application.Middleware_1'].post_dispatch
        assert middleware_2['handle_exception'][0] == factory.instances['test_application.Middleware_1'].handle_exception

    def test_load_reversed_middleware(self):
        factory = MiddlewareFactory()
        middleware = factory.load_middleware([Middleware_3, Middleware_4, Middleware_5])

        assert len(factory.instances) == 3
        assert len(factory.methods) == 3

        assert 'test_application.Middleware_3' in factory.instances
        assert 'test_application.Middleware_4' in factory.instances
        assert 'test_application.Middleware_5' in factory.instances

        assert 'test_application.Middleware_3' in factory.methods
        assert 'test_application.Middleware_4' in factory.methods
        assert 'test_application.Middleware_5' in factory.methods

        assert 'post_run_app' in middleware
        assert 'post_dispatch' in middleware
        assert 'handle_exception' in middleware

        # Now, these method should be in reverse order...
        assert middleware['post_run_app'][0] == factory.instances['test_application.Middleware_5'].post_run_app
        assert middleware['post_run_app'][1] == factory.instances['test_application.Middleware_4'].post_run_app
        assert middleware['post_run_app'][2] == factory.instances['test_application.Middleware_3'].post_run_app

        assert middleware['post_dispatch'][0] == factory.instances['test_application.Middleware_5'].post_dispatch
        assert middleware['post_dispatch'][1] == factory.instances['test_application.Middleware_4'].post_dispatch
        assert middleware['post_dispatch'][2] == factory.instances['test_application.Middleware_3'].post_dispatch

        assert middleware['handle_exception'][0] == factory.instances['test_application.Middleware_5'].handle_exception
        assert middleware['handle_exception'][1] == factory.instances['test_application.Middleware_4'].handle_exception
        assert middleware['handle_exception'][2] == factory.instances['test_application.Middleware_3'].handle_exception


class TestWSGIApplication(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()


class TestMiscelaneous(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_make_wsgi_app(self):
        app = tipfy.make_wsgi_app({'tipfy': {
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

    def test_set_extensions_compatibility(self):
        extensions = [
            'tipfy.ext.debugger',
            'tipfy.ext.appstats',
            'tipfy.ext.i18n',
            'tipfy.ext.session',
            'tipfy.ext.user',
        ]
        middleware = []
        set_extensions_compatibility(extensions, middleware)

        assert extensions == []
        assert middleware == [
            'tipfy.ext.debugger.DebuggerMiddleware',
            'tipfy.ext.appstats.AppstatsMiddleware',
            'tipfy.ext.session.SessionMiddleware',
            'tipfy.ext.auth.AuthMiddleware',
            'tipfy.ext.i18n.I18nMiddleware',
        ]

        extensions = [
            'tipfy.ext.debugger',
            'tipfy.ext.appstats',
            'tipfy.ext.i18n',
            'tipfy.ext.user',
        ]
        middleware = []
        set_extensions_compatibility(extensions, middleware)

        assert extensions == []
        assert middleware == [
            'tipfy.ext.debugger.DebuggerMiddleware',
            'tipfy.ext.appstats.AppstatsMiddleware',
            'tipfy.ext.session.SessionMiddleware',
            'tipfy.ext.auth.AuthMiddleware',
            'tipfy.ext.i18n.I18nMiddleware',
        ]
