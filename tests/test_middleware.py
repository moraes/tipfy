import unittest

from tipfy import MiddlewareFactory, Tipfy


class SomeObject(object):
    pass


class Middleware_1(object):
    def post_make_app(self, app):
        return app

    def pre_dispatch_handler(self):
        pass

    def post_dispatch_handler(self, response):
        pass

    def pre_dispatch(self):
        pass

    def post_dispatch(self, response):
        pass


class Middleware_2(object):
    def post_make_app(self, app):
        return app


class Middleware_3(object):
    def post_dispatch_handler(self, response):
        pass

    def post_dispatch(self, response):
        pass


class Middleware_4(object):
    def post_dispatch_handler(self, response):
        pass

    def post_dispatch(self, response):
        pass


class Middleware_5(object):
    def post_dispatch_handler(self, response):
        pass

    def post_dispatch(self, response):
        pass


class TestMiddlewareFactory(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_get_middleware(self):
        factory = MiddlewareFactory()
        obj = SomeObject()
        middleware = factory.get_middleware(obj, [Middleware_1, Middleware_2])

        assert len(factory.obj_middleware) == 1
        assert len(factory.instances) == 2
        assert len(factory.methods) == 2

        assert __name__ + '.SomeObject' in factory.obj_middleware

        assert __name__ + '.Middleware_1' in factory.instances
        assert __name__ + '.Middleware_2' in factory.instances

        assert __name__ + '.Middleware_1' in factory.methods
        assert __name__ + '.Middleware_2' in factory.methods

        assert 'post_make_app' in middleware
        assert 'pre_dispatch_handler' in middleware
        assert 'post_dispatch_handler' in middleware
        assert 'pre_dispatch' in middleware
        assert 'post_dispatch' in middleware

        assert len(middleware['post_make_app']) == 2
        assert len(middleware['pre_dispatch_handler']) == 1
        assert len(middleware['post_dispatch_handler']) == 1
        assert len(middleware['pre_dispatch']) == 1
        assert len(middleware['post_dispatch']) == 1

        assert middleware['post_make_app'][0] == factory.instances[__name__ + '.Middleware_1'].post_make_app
        assert middleware['post_make_app'][1] == factory.instances[__name__ + '.Middleware_2'].post_make_app
        assert middleware['pre_dispatch_handler'][0] == factory.instances[__name__ + '.Middleware_1'].pre_dispatch_handler
        assert middleware['post_dispatch_handler'][0] == factory.instances[__name__ + '.Middleware_1'].post_dispatch_handler
        assert middleware['pre_dispatch'][0] == factory.instances[__name__ + '.Middleware_1'].pre_dispatch
        assert middleware['post_dispatch'][0] == factory.instances[__name__ + '.Middleware_1'].post_dispatch

        assert len(factory.obj_middleware[__name__ + '.SomeObject']['post_make_app']) == 2
        assert len(factory.obj_middleware[__name__ + '.SomeObject']['pre_dispatch_handler']) == 1
        assert len(factory.obj_middleware[__name__ + '.SomeObject']['post_dispatch_handler']) == 1
        assert len(factory.obj_middleware[__name__ + '.SomeObject']['pre_dispatch']) == 1
        assert len(factory.obj_middleware[__name__ + '.SomeObject']['post_dispatch']) == 1

        assert factory.obj_middleware[__name__ + '.SomeObject']['post_make_app'][0] == factory.instances[__name__ + '.Middleware_1'].post_make_app
        assert factory.obj_middleware[__name__ + '.SomeObject']['post_make_app'][1] == factory.instances[__name__ + '.Middleware_2'].post_make_app
        assert factory.obj_middleware[__name__ + '.SomeObject']['pre_dispatch_handler'][0] == factory.instances[__name__ + '.Middleware_1'].pre_dispatch_handler
        assert factory.obj_middleware[__name__ + '.SomeObject']['post_dispatch_handler'][0] == factory.instances[__name__ + '.Middleware_1'].post_dispatch_handler
        assert factory.obj_middleware[__name__ + '.SomeObject']['pre_dispatch'][0] == factory.instances[__name__ + '.Middleware_1'].pre_dispatch
        assert factory.obj_middleware[__name__ + '.SomeObject']['post_dispatch'][0] == factory.instances[__name__ + '.Middleware_1'].post_dispatch

    def test_load_middleware(self):
        factory = MiddlewareFactory()
        middleware = factory.load_middleware([Middleware_1, Middleware_2])
        middleware_2 = factory.load_middleware([Middleware_1, Middleware_2])

        assert len(factory.instances) == 2
        assert len(factory.methods) == 2

        assert __name__ + '.Middleware_1' in factory.instances
        assert __name__ + '.Middleware_2' in factory.instances

        assert __name__ + '.Middleware_1' in factory.methods
        assert __name__ + '.Middleware_2' in factory.methods

        assert 'post_make_app' in middleware
        assert 'pre_dispatch_handler' in middleware
        assert 'post_dispatch_handler' in middleware
        assert 'pre_dispatch' in middleware
        assert 'post_dispatch' in middleware

        assert len(middleware['post_make_app']) == 2
        assert len(middleware['pre_dispatch_handler']) == 1
        assert len(middleware['post_dispatch_handler']) == 1
        assert len(middleware['pre_dispatch']) == 1
        assert len(middleware['post_dispatch']) == 1

        assert middleware['post_make_app'][0] == factory.instances[__name__ + '.Middleware_1'].post_make_app
        assert middleware['post_make_app'][1] == factory.instances[__name__ + '.Middleware_2'].post_make_app
        assert middleware['pre_dispatch_handler'][0] == factory.instances[__name__ + '.Middleware_1'].pre_dispatch_handler
        assert middleware['post_dispatch_handler'][0] == factory.instances[__name__ + '.Middleware_1'].post_dispatch_handler
        assert middleware['pre_dispatch'][0] == factory.instances[__name__ + '.Middleware_1'].pre_dispatch
        assert middleware['post_dispatch'][0] == factory.instances[__name__ + '.Middleware_1'].post_dispatch

        assert 'post_make_app' in middleware_2
        assert 'pre_dispatch_handler' in middleware_2
        assert 'post_dispatch_handler' in middleware_2
        assert 'pre_dispatch' in middleware_2
        assert 'post_dispatch' in middleware_2

        assert len(middleware_2['post_make_app']) == 2
        assert len(middleware_2['pre_dispatch_handler']) == 1
        assert len(middleware_2['post_dispatch_handler']) == 1
        assert len(middleware_2['pre_dispatch']) == 1
        assert len(middleware_2['post_dispatch']) == 1

        assert middleware_2['post_make_app'][0] == factory.instances[__name__ + '.Middleware_1'].post_make_app
        assert middleware_2['post_make_app'][1] == factory.instances[__name__ + '.Middleware_2'].post_make_app
        assert middleware_2['pre_dispatch_handler'][0] == factory.instances[__name__ + '.Middleware_1'].pre_dispatch_handler
        assert middleware_2['post_dispatch_handler'][0] == factory.instances[__name__ + '.Middleware_1'].post_dispatch_handler
        assert middleware_2['pre_dispatch'][0] == factory.instances[__name__ + '.Middleware_1'].pre_dispatch
        assert middleware_2['post_dispatch'][0] == factory.instances[__name__ + '.Middleware_1'].post_dispatch

    def test_load_middleware_using_strings(self):
        factory = MiddlewareFactory()
        middleware = factory.load_middleware(['test_middleware.Middleware_1', 'test_middleware.Middleware_2'])
        middleware_2 = factory.load_middleware(['test_middleware.Middleware_1', 'test_middleware.Middleware_2'])

        assert len(factory.instances) == 2
        assert len(factory.methods) == 2

        assert 'test_middleware.Middleware_1' in factory.instances
        assert 'test_middleware.Middleware_2' in factory.instances

        assert 'test_middleware.Middleware_1' in factory.methods
        assert 'test_middleware.Middleware_2' in factory.methods

        assert 'post_make_app' in middleware
        assert 'pre_dispatch_handler' in middleware
        assert 'post_dispatch_handler' in middleware
        assert 'pre_dispatch' in middleware
        assert 'post_dispatch' in middleware

        assert len(middleware['post_make_app']) == 2
        assert len(middleware['pre_dispatch_handler']) == 1
        assert len(middleware['post_dispatch_handler']) == 1
        assert len(middleware['pre_dispatch']) == 1
        assert len(middleware['post_dispatch']) == 1

        assert middleware['post_make_app'][0] == factory.instances['test_middleware.Middleware_1'].post_make_app
        assert middleware['post_make_app'][1] == factory.instances['test_middleware.Middleware_2'].post_make_app
        assert middleware['pre_dispatch_handler'][0] == factory.instances['test_middleware.Middleware_1'].pre_dispatch_handler
        assert middleware['post_dispatch_handler'][0] == factory.instances['test_middleware.Middleware_1'].post_dispatch_handler
        assert middleware['pre_dispatch'][0] == factory.instances['test_middleware.Middleware_1'].pre_dispatch
        assert middleware['post_dispatch'][0] == factory.instances['test_middleware.Middleware_1'].post_dispatch

        assert 'post_make_app' in middleware_2
        assert 'pre_dispatch_handler' in middleware_2
        assert 'post_dispatch_handler' in middleware_2
        assert 'pre_dispatch' in middleware_2
        assert 'post_dispatch' in middleware_2

        assert len(middleware_2['post_make_app']) == 2
        assert len(middleware_2['pre_dispatch_handler']) == 1
        assert len(middleware_2['post_dispatch_handler']) == 1
        assert len(middleware_2['pre_dispatch']) == 1
        assert len(middleware_2['post_dispatch']) == 1

        assert middleware_2['post_make_app'][0] == factory.instances['test_middleware.Middleware_1'].post_make_app
        assert middleware_2['post_make_app'][1] == factory.instances['test_middleware.Middleware_2'].post_make_app
        assert middleware_2['pre_dispatch_handler'][0] == factory.instances['test_middleware.Middleware_1'].pre_dispatch_handler
        assert middleware_2['post_dispatch_handler'][0] == factory.instances['test_middleware.Middleware_1'].post_dispatch_handler
        assert middleware_2['pre_dispatch'][0] == factory.instances['test_middleware.Middleware_1'].pre_dispatch
        assert middleware_2['post_dispatch'][0] == factory.instances['test_middleware.Middleware_1'].post_dispatch

    def test_load_reversed_middleware(self):
        factory = MiddlewareFactory()
        middleware = factory.load_middleware([Middleware_3, Middleware_4, Middleware_5])

        assert len(factory.instances) == 3
        assert len(factory.methods) == 3

        assert __name__ + '.Middleware_3' in factory.instances
        assert __name__ + '.Middleware_4' in factory.instances
        assert __name__ + '.Middleware_5' in factory.instances

        assert __name__ + '.Middleware_3' in factory.methods
        assert __name__ + '.Middleware_4' in factory.methods
        assert __name__ + '.Middleware_5' in factory.methods

        assert 'post_dispatch_handler' in middleware
        assert 'post_dispatch' in middleware

        # Now, these method should be in reverse order...
        assert middleware['post_dispatch_handler'][0] == factory.instances[__name__ + '.Middleware_5'].post_dispatch_handler
        assert middleware['post_dispatch_handler'][1] == factory.instances[__name__ + '.Middleware_4'].post_dispatch_handler
        assert middleware['post_dispatch_handler'][2] == factory.instances[__name__ + '.Middleware_3'].post_dispatch_handler

        assert middleware['post_dispatch'][0] == factory.instances[__name__ + '.Middleware_5'].post_dispatch
        assert middleware['post_dispatch'][1] == factory.instances[__name__ + '.Middleware_4'].post_dispatch
        assert middleware['post_dispatch'][2] == factory.instances[__name__ + '.Middleware_3'].post_dispatch
