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

from werkzeug import Request as WerkzeugRequest, Response as WerkzeugResponse

from tipfy import (default_config, local, local_manager, HTTPException,
    import_string, InternalServerError, Map, MethodNotAllowed, NotFound,
    RequestRedirect)
from tipfy.config import Config

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
    #: middleware can implement three methods that are called before and after
    #: the current request method is executed, or if an exception occurs:
    #: ``pre_dispatch(handler)``, ``post_dispatch(handler, response)`` and
    #: ``handle_exception(exception, handler)``. They can initialize features,
    #: post-process the response and handle errors in a per handler basis.
    middleware = []

    def dispatch(self, *args, **kwargs):
        """Executes a handler method. This method is called by the
        WSGIApplication and must always return a response object.

        :param request:
            The method to be executed.
        :param kwargs:
            The arguments from the matched route.
        :return:
            A ``werkzeug.Response`` object.
        """
        if len(args) == 1:
            # For backwards compatibility only. Previously dispatch signature
            # was dispatch(request_method, **rule_args).
            action = args[0]
            rule_args = kwargs
        else:
            self.request = local.request
            action = self.request.method.lower()
            rule_args = self.request.rule_args

        method = getattr(self, action, None)
        if method is None:
            raise MethodNotAllowed()

        if not self.middleware:
            # No middleware is set: only execute the method.
            return method(**rule_args)

        # Get middleware for this handler.
        middleware = local.app.middleware_factory.get_middleware(self,
            self.middleware)

        # Execute pre_dispatch middleware.
        for hook in middleware.get('pre_dispatch', []):
            response = hook(self)
            if response is not None:
                break
        else:
            try:
                # Execute the requested method.
                response = method(**rule_args)
            except Exception, e:
                # Execute handle_exception middleware.
                for hook in middleware.get('handle_exception', []):
                    response = hook(e, self)
                    if response is not None:
                        break
                else:
                    raise

        # Execute post_dispatch middleware.
        for hook in middleware.get('post_dispatch', []):
            response = hook(self, response)

        # Done!
        return response


class Request(WerkzeugRequest):
    """The ``Request`` object contains all environment variables for the
    current request: GET, POST, FILES, cookies and headers. Additionally
    it will match the current URL and store information about the matched
    ``Rule``, and make sure that the requested HTTP method is allowed on
    Google App Engine.
    """
    #: URL adapter bound to the request.
    url_adapter = None
    #: Matched URL Rule for this request.
    rule = None
    #: Arguments from the matched Rule.
    rule_args = None

    def __init__(self, environ):
        super(WerkzeugRequest, self).__init__(environ)

        # Check that the requested method is allowed in App Engine.
        if self.method.lower() not in ALLOWED_METHODS:
            raise MethodNotAllowed()

    def match_url(self, app):
        """Matches current URL and returns a callable to be used by
        the WSGI application. If no URL matches, returns ``None``.

        :param app:
            A :class:`WSGIApplication` instance.
        :return:
            A callable to execute the matched handler. This will return
            :meth:`RequestHandler.dispatch`, but alternative implementations
            could load the handler differently (use simple functions instead
            of classes or other strategies).
        :raises:
            ``NotFound``, ``MethodNotAllowed`` or ``RequestRedirect``
            exceptions, which should be caught by the application.
        """
        # For backwards compatibility only. Previously these were app
        # attributes.
        app.rule = app.rule_args = None

        # Bind url map to the current request location.
        server_name = app.config.get('tipfy', 'server_name', None)
        subdomain = app.config.get('tipfy', 'subdomain', None)
        self.url_adapter = app.url_adapter = app.url_map.bind_to_environ(
            self.environ, server_name=server_name, subdomain=subdomain)

        # Match the path against registered rules.
        self.rule, self.rule_args = self.url_adapter.match(self.path,
            return_rule=True)

        name = self.rule.handler
        if name not in app.handlers:
            # Import handler set in matched rule.
            app.handlers[name] = import_string(name)

        # For backwards compatibility only.
        app.rule = self.rule
        app.rule_args = self.rule_args

        # Returns a callable to execute the handler.
        return app.handlers[name]().dispatch


class Response(WerkzeugResponse):
    """A `werkzeug.Response` with default mimetype set to 'text/html'."""
    default_mimetype = 'text/html'


class MiddlewareFactory(object):
    """A factory and registry for middleware instances in use."""
    names = (
        'post_make_app',
        'pre_run_app',
        'pre_dispatch_handler',
        'post_dispatch_handler',
        'pre_dispatch',
        'post_dispatch',
        'handle_exception',
    )
    reverse_names = (
        'post_dispatch_handler',
        'post_dispatch',
        'handle_exception',
    )

    def __init__(self):
        # Instantiated middleware.
        self.instances = {}
        # Methods from instantiated middleware.
        self.methods = {}
        # Middleware methods for a given object.
        self.obj_middleware = {}

    def get_middleware(self, obj, classes):
        """Returns a dictionary of all middleware instance methods for a given
        object.

        :param obj:
            The object to search for related middleware (the
            ``WSGIApplication`` or ``RequestHandler``).
        :param classes:
            A list of middleware classes.
        :return:
            A dictionary with middleware instance methods.
        """
        id = obj.__module__ + '.' + obj.__class__.__name__

        if id not in self.obj_middleware:
            self.obj_middleware[id] = self.load_middleware(classes)

        return self.obj_middleware[id]

    def load_middleware(self, classes):
        """Returns a dictionary of middleware instance methods for a list of
        classes.

        :param classes:
            A list of middleware classes.
        :return:
            A dictionary with middleware instance methods.
        """
        res = {}

        for cls in classes:
            if isinstance(cls, basestring):
                id = cls
            else:
                id = cls.__module__ + '.' + cls.__name__

            if id not in self.methods:
                if isinstance(cls, basestring):
                    cls = import_string(cls)

                obj = cls()
                self.instances[id] = obj
                self.methods[id] = [getattr(obj, n, None) for n in self.names]

            for name, method in zip(self.names, self.methods[id]):
                if method:
                    res.setdefault(name, []).append(method)

        for name in self.reverse_names:
            if name in res:
                res[name].reverse()

        return res


class WSGIApplication(object):
    """The WSGI application which centralizes URL dispatching, configuration
    and hooks for an App Rngine app.
    """
    #: Default class for requests.
    request_class = Request
    #: Default class for responses.
    response_class = Response

    def __init__(self, config=None):
        """Initializes the application.

        :param config:
            Dictionary with configuration for the application modules.
        """
        # Set an accessor to this instance.
        local.app = self

        # Load default config and update with values for this instance.
        self.config = Config(config)
        self.config.setdefault('tipfy', default_config)

        # Set a shortcut to the development flag.
        self.dev = self.config.get('tipfy', 'dev', False)

        # Set the url rules.
        self.url_map = self.config.get('tipfy', 'url_map')
        if not self.url_map:
            self.url_map = self.get_url_map()

        # Cache for loaded handler classes.
        self.handlers = {}

        extensions = self.config.get('tipfy', 'extensions')
        middleware = self.config.get('tipfy', 'middleware')
        if extensions:
            # For backwards compatibility only.
            set_extensions_compatibility(extensions, middleware)

        # Middleware factory and registry.
        self.middleware_factory = factory = MiddlewareFactory()

        # Store the app middleware dict.
        self.middleware = factory.get_middleware(self, middleware)

    def __call__(self, environ, start_response):
        """Shortcut for :attr:`wsgi_app`"""
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        """The actual WSGI application.  This is not implemented in
        `__call__` so that middlewares can be applied without losing a
        reference to the class.  So instead of doing this::

            app = MyMiddleware(app)

        It's a better idea to do this instead::

            app.wsgi_app = MyMiddleware(app.wsgi_app)

        Then you still have the original application object around and
        can continue to call methods on it.

        :param environ:
            A WSGI environment.
        :param start_response:
            A callable accepting a status code, a list of headers and
            an optional exception context to start the response
        """
        cleanup = True
        try:
            # Set local variables for a single request.
            local.app = self
            local.request = self.request_class(environ)
            # Kept here for backwards compatibility.
            local.response = self.response_class()

            # Execute pre_dispatch_handler middleware.
            for hook in self.middleware.get('pre_dispatch_handler', []):
                rv = hook()
                if rv is not None:
                    break
            else:
                # Match the path against registered rules.
                handler = local.request.match_url(self)
                # Instantiate handler and dispatch request method.
                rv = handler()

            # Build a response using the returned value.
            response = self.make_response(rv)

            # Execute post_dispatch_handler middleware.
            for hook in self.middleware.get('post_dispatch_handler', []):
                response = hook(response)

        except RequestRedirect, e:
            # Execute redirects raised by the routing system or the
            # application.
            response = e
        except Exception, e:
            # Handle HTTP and uncaught exceptions.
            cleanup = not self.dev
            response = self.handle_exception(e)
        finally:
            # Do not clean local if we are in development mode and an
            # exception happened. This allows the debugger to still access
            # request and other variables from local in the interactive shell.
            if cleanup:
                local_manager.cleanup()

        # Call the response object as a WSGI application.
        return response(environ, start_response)

    def make_response(self, rv):
        """Converts the return value from a view function to a real
        response object that is an instance of :attr:`response_class`.

        The following types are allowd for `rv`:

        ======================= ===========================================
        :attr:`response_class`  the object is returned unchanged
        :class:`str`            a response object is created with the
                                string as body
        :class:`unicode`        a response object is created with the
                                string encoded to utf-8 as body
        :class:`tuple`          the response object is created with the
                                contents of the tuple as arguments
        a WSGI function         the function is called as WSGI application
                                and buffered as response object
        ======================= ===========================================

        This function comes from `Flask`_.

        :param rv: the return value from the view function
        """
        if isinstance(rv, self.response_class):
            return rv

        if isinstance(rv, basestring):
            return self.response_class(rv)

        if isinstance(rv, tuple):
            return self.response_class(*rv)

        return self.response_class.force_type(rv, local.request.environ)

    def get_url_map(self):
        """Returns ``werkzeug.routing.Map`` with the URL rules defined for the
        application. Rules are cached in production; the cache is automatically
        renewed on each deployment.

        :return:
            A ``werkzeug.routing.Map`` instance.
        """
        rules = import_string('urls.get_rules')()
        kwargs = self.config.get('tipfy').get('url_map_kwargs')
        return Map(rules, **kwargs)

    def handle_exception(self, e):
        """Handles HTTPException or uncaught exceptions raised by the WSGI
        application, optionally applying exception middleware.

        :param e:
            The catched exception.
        :return:
            A ``werkzeug.Response`` object, if the exception is not raised.
        """
        # Execute handle_exception middleware.
        for hook in self.middleware.get('handle_exception', []):
            response = hook(e)
            if response:
                return response

        logging.exception(e)

        if self.dev:
            raise

        if isinstance(e, HTTPException):
            return e

        return InternalServerError()


def make_wsgi_app(config):
    """Returns a instance of :class:`WSGIApplication`.

    :param config:
        A dictionary of configuration values.
    :return:
        A :class:`WSGIApplication` instance.
    """
    app = WSGIApplication(config)

    if app.config.get('debug'):
        logging.getLogger().setLevel(logging.DEBUG)

    # Execute post_make_app middleware.
    for hook in app.middleware.get('post_make_app', []):
        app = hook(app)

    return app


def run_wsgi_app(app):
    """Executes the application, optionally wrapping it by middleware.

    :param app:
        A :class:`WSGIApplication` instance.
    :return:
        ``None``.
    """
    # Fix issue #772.
    if app.dev:
        fix_sys_path()

    # Execute pre_run_app middleware.
    for hook in app.middleware.get('pre_run_app', []):
        app = hook(app)

    # Run it.
    CGIHandler().run(app)


def set_extensions_compatibility(extensions, middleware):
    """Starting at version 0.5, the "extensions" setting from config was
    deprecated in favor of a unified middleware system for the WSGI app and
    handlers. This functions checks for common extensions available pre-0.5
    and sets the equivalent middleware classes instead.

    :param extensions:
        List of extensions set in config.
    :param middleware:
        List of middleware set in config.
    """
    logging.warning('The "extensions" setting from config is deprecated. '
        'Use the "middleware" setting instead.')

    conversions = [
        ('tipfy.ext.debugger', ['tipfy.ext.debugger.DebuggerMiddleware']),
        ('tipfy.ext.appstats', ['tipfy.ext.appstats.AppstatsMiddleware']),
        ('tipfy.ext.session',  ['tipfy.ext.session.SessionMiddleware']),
        ('tipfy.ext.user',     ['tipfy.ext.session.SessionMiddleware',
                                'tipfy.ext.auth.AuthMiddleware']),
        ('tipfy.ext.i18n',     ['tipfy.ext.i18n.I18nMiddleware']),
    ]

    for old, new in conversions:
        if old in extensions:
            extensions.remove(old)
            for m in new:
                if m not in middleware:
                    middleware.append(m)

    if extensions:
        logging.warning('The following extensions were not '
            'loaded: %s' % str(extensions))


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
           'Request',
           'RequestHandler',
           'run_wsgi_app',
           'WSGIApplication']
