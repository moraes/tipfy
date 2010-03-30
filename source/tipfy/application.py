# -*- coding: utf-8 -*-
"""
    tipfy.application
    ~~~~~~~~~~~~~~~~~

    WSGI application and base request handler.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import logging
from wsgiref.handlers import CGIHandler

from werkzeug import ClosingIterator, Request, Response

from tipfy import (default_config, local, local_manager, HTTPException,
    import_string, InternalServerError, Map, MethodNotAllowed, RequestRedirect)
from tipfy import config
from tipfy import hooks

# Allowed request methods.
ALLOWED_METHODS = frozenset(['get', 'post', 'head', 'options', 'put', 'delete',
    'trace'])


class RequestHandler(object):
    """Base request handler. Implements the minimal interface required by
    :class:`WSGIApplication`: the ``dispatch()`` method.

    Additionally, implements a middleware system to pre and post process
    requests and handle exceptions.
    """
    #: A list of classes or callables that return a middleware object. A
    #: middleware can implement two methods that are called before and after
    #: the current request method is executed in the handler:
    #: ``pre_dispatch(handler)`` and ``post_dispatch(handler, response)``.
    #: They are useful to initialize features and post-process the response in
    #: a per handler basis.
    middleware = []

    def dispatch(self, action, *args, **kwargs):
        """Executes a handler method. This method is called by the
        WSGIApplication and must always return a response object.

        :param action:
            The method to be executed.
        :param kwargs:
            The arguments from the matched route.
        :return:
            A ``werkzeug.Response`` object.
        """
        method = getattr(self, action, None)
        if method is None:
            raise MethodNotAllowed()

        if not self.middleware:
            # No middleware is set: only execute the method.
            return method(*args, **kwargs)

        # Get middleware for this handler.
        middleware = local.app.middleware.get_handler_middleware(self)

        # Execute pre_dispatch middleware.
        for func in middleware.get('pre_dispatch'):
            response = func(self)
            if response is not None:
                break
        else:
            try:
                # Execute the requested method.
                response = method(*args, **kwargs)
            except Exception, e:
                # Execute handle_exception middleware.
                for func in middleware.get('handle_exception'):
                    response = func(self, e)
                    if response:
                        return response
                else:
                    raise

        # Execute post_dispatch() middleware.
        for func in middleware.get('post_dispatch'):
            response = func(self, response)

        # Done!
        return response


class MiddlewareFactory(object):
    """A factory and registry for handler middleware instances in use."""
    types = ('pre_dispatch', 'handle_exception', 'post_dispatch')

    def __init__(self):
        # Instantiated middleware.
        self.instances = {}
        # Methods from instantiated middleware.
        self.instance_methods = {}
        # Middleware methods for a given handler.
        self.handler_middleware = {}

    def get_instance_methods(self, cls):
        """Returns the instance methods of a given middleware class.

        :param cls:
            A middleware class.
        :return:
            A list with the instance methods ``[pre_dispatch, handle_exception,
            post_dispatch]`` from the given middleware class. If the class
            doesn't have a method, the position is set to ``None``.
        """
        if isinstance(cls, basestring):
            cls = import_string(cls)

        id = cls.__module__ + '.' + cls.__name__

        if id not in self.instances:
            obj = cls()
            self.instances[id] = obj
            self.instance_methods[id] = [getattr(obj, t, None) for t in \
                self.types]

        return self.instance_methods[id]

    def get_handler_middleware(self, handler):
        """Returns the a dictionary of middleware instance methods for a
        handler.

        :param handler:
            A class:`tipfy.RequestHandler` instance.
        :return:
            A dictionary with handler middleware methods.
        """
        id = handler.__module__ + '.' + handler.__class__.__name__

        if id not in self.handler_middleware:
            res = {
                'pre_dispatch': [],
                'handle_exception': [],
                'post_dispatch': []
            }

            for cls in handler.middleware:
                methods = self.get_instance_methods(cls)
                for i, name in enumerate(self.types):
                    if methods[i]:
                        res[name].append(methods[i])

            res['handle_exception'].reverse()
            res['post_dispatch'].reverse()
            self.handler_middleware[id] = res

        return self.handler_middleware[id]


class WSGIApplication(object):
    """The WSGI application which centralizes URL dispatching, configuration
    and hooks for an App Rngine app.
    """
    #: Default class for requests.
    request_class = Request
    #: Default class for responses.
    response_class = Response

    def __init__(self, app_config=None):
        """Initializes the application.

        :param app_config:
            Dictionary with configuration for the application modules.
        """
        # Set an accessor to this instance.
        local.app = self

        # Load default config and update with values for this instance.
        self.config = config.Config(app_config)
        self.config.setdefault('tipfy', default_config)

        # Set the url rules.
        self.url_map = self.config.get('tipfy', 'url_map')
        if not self.url_map:
            self.url_map = self.get_url_map()

        # Cache for loaded handler classes.
        self.handlers = {}

        # Set the hook handler.
        self.hooks = hooks.HookHandler()

        # Start a middleware manager for handlers.
        self.middleware = MiddlewareFactory()

        # Setup extensions.
        for module in self.config.get('tipfy', 'extensions', []):
            import_string(module + ':setup')(self)

    def __call__(self, environ, start_response):
        """Called by WSGI when a request comes in."""
        try:
            return self.dispatch(environ, start_response)
        finally:
            local_manager.cleanup()

    def dispatch(self, environ, start_response):
        # Set local variables for a single request.
        local.app = self
        local.request = request = self.request_class(environ)
        local.response = self.response_class()

        # Bind url map to the current request location.
        self.url_adapter = self.url_map.bind_to_environ(environ,
            server_name=self.config.get('tipfy', 'server_name', None),
            subdomain=self.config.get('tipfy', 'subdomain', None))

        self.rule = self.rule_args = None

        try:
            # Check requested method.
            method = request.method.lower()
            if method not in ALLOWED_METHODS:
                raise MethodNotAllowed()

            # Match the path against registered rules.
            self.rule, self.rule_args = self.url_adapter.match(request.path,
                return_rule=True)

            # Apply pre-dispatch hooks.
            for response in self.hooks.iter('pre_dispatch_handler'):
                if response is not None:
                    break
            else:
                # Import handler set in matched rule.
                name = self.rule.handler
                if name not in self.handlers:
                    self.handlers[name] = import_string(name)

                # Instantiate handler and dispatch request method.
                response = self.handlers[name]().dispatch(method,
                    **self.rule_args)

            # Apply post-dispatch hooks.
            for res in self.hooks.iter('post_dispatch_handler', response):
                if res is not None:
                    response = res
                    break

        except RequestRedirect, e:
            # Execute redirects raised by the routing system or the application.
            response = e
        except Exception, e:
            # Handle http and uncaught exceptions. This will apply exception
            # hooks if they are set.
            response = self.handle_exception(e)

        # Call the response object as a WSGI application.
        return response(environ, start_response)

    def get_url_map(self):
        """Returns ``werkzeug.routing.Map`` with the URL rules defined for the
        application. Rules are cached in production; the cache is automatically
        renewed on each deployment.

        :return:
            A ``werkzeug.routing.Map`` instance.
        """
        rules = import_string('urls:get_rules')()
        kwargs = self.config.get('tipfy').get('url_map_kwargs')

        return Map(rules, **kwargs)

    def handle_exception(self, e):
        """Handles HTTPException or uncaught exceptions raised by the WSGI
        application, optionally applying exception hooks.

        :param e:
            The catched exception.
        :return:
            A ``werkzeug.Response`` object, if the exception is not raised.
        """
        # Apply pre_handle_exception hooks.
        for response in self.hooks.iter('pre_handle_exception', e):
            if response:
                return response

        logging.exception(e)

        if self.config.get('tipfy', 'dev'):
            raise

        if isinstance(e, HTTPException):
            return e

        return InternalServerError()


class PatchedCGIHandler(CGIHandler):
    """``wsgiref.handlers.CGIHandler`` holds ``os.environ`` when imported. This
    class overrides this behaviour. Thanks to Kay framework for this patch.
    """
    def __init__(self):
        self.os_environ = {}
        CGIHandler.__init__(self)


def make_wsgi_app(config):
    """Returns a instance of :class:`WSGIApplication`.

    :param config:
        A dictionary of configuration values.
    :return:
        A :class:`WSGIApplication` instance.
    """
    app = WSGIApplication(config)

    # Apply post_make_app hooks.
    for hook in app.hooks.get('post_make_app', []):
        app = hook(app) or app

    return app


def run_wsgi_app(app):
    """Executes the application, optionally wrapping it by hooks.

    :param app:
        A :class:`WSGIApplication` instance.
    :return:
        ``None``.
    """
    # Fix issue #772.
    if app.config.get('tipfy', 'dev'):
        fix_sys_path()

    # Apply pre_run_app hooks.
    # Note: using app.hooks.iter caused only the last middleware
    #   to get applied instead of chaining the middleware
    for hook in app.hooks.get('pre_run_app', []):
        app = hook(app) or app

    # Run it.
    PatchedCGIHandler().run(app)


_ULTIMATE_SYS_PATH = None
def fix_sys_path():
    """A fix for issue 772. We must keep this here until it is fixed in the dev
    server.

    See: http://code.google.com/p/googleappengine/issues/detail?id=772
    """
    global _ULTIMATE_SYS_PATH
    import sys
    if _ULTIMATE_SYS_PATH is None:
        _ULTIMATE_SYS_PATH = list(sys.path)
    elif sys.path != _ULTIMATE_SYS_PATH:
        sys.path[:] = _ULTIMATE_SYS_PATH


__all__ = ['make_wsgi_app',
           'MiddlewareFactory',
           'RequestHandler',
           'run_wsgi_app',
           'WSGIApplication']
