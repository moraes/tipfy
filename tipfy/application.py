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

from werkzeug import (Request as WerkzeugRequest, Response as WerkzeugResponse,
    url_quote)

from tipfy import (default_config, HTTPException, import_string,
    InternalServerError, local, Map, MethodNotAllowed, NotFound,
    RequestRedirect)

# Allowed request methods.
ALLOWED_METHODS = frozenset(['get', 'post', 'head', 'options', 'put', 'delete',
    'trace'])
# Value used for required values.
REQUIRED_VALUE = object()
# Value used for missing default values.
DEFAULT_VALUE = object()


class RequestHandler(object):
    """Base request handler. Implements the minimal interface required by
    :class:`Tipfy`: the ``dispatch()`` method.

    Additionally, implements a middleware system to pre and post process
    requests and handle exceptions.
    """
    #: A list of middleware classes or callables. A middleware can implement
    #: three methods that are called before and after
    #: the current request method is executed, or if an exception occurs:
    #: ``pre_dispatch(handler)``: Called before the requested method is
    #:     executed. If returns a response, stops the middleware chain and
    #:     uses that response, not calling the requested method.
    #: ``post_dispatch(exception, handler)``: Called after the requested
    #;     method is executed. Must always return a response. All
    #:     ``post_dispatch`` middleware are always executed.
    #: ``handle_exception(exception, handler)``: Called if an exception occurs.
    middleware = []

    def __init__(self, app, request):
        """Initializes the handler.

        :param app:
            A :class:`Tipfy` instance.
        :param request:
            A :class:`Request` instance.
        """
        self.app = app
        self.request = request

    def dispatch(self, *args, **kwargs):
        """Executes a handler method. This method is called by :class:`Tipfy`
        and must return a :class:`Response` object.

        :return:
            A :class:`Response` instance.
        """
        if len(args) == 1:
            # For backwards compatibility only.
            action = args[0]
            rule_args = kwargs
        else:
            action = self.request.method.lower()
            rule_args = self.request.rule_args

        method = getattr(self, action, None)
        if method is None:
            raise MethodNotAllowed()

        if not self.middleware:
            # No middleware is set: just execute the method.
            return method(**rule_args)

        # Get all middleware for this handler.
        middleware = self.app.get_middleware(self, self.middleware)

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


class Context(dict):
    """A simple registry for global values in use by :class::`Tipfy`
    and :class:`Request`.
    """


class Request(WerkzeugRequest):
    """The ``Request`` object contains all environment variables for the
    current request: GET, POST, FILES, cookies and headers. Additionally
    it stores the URL adapter bound to the request and information about the
    matched URL rule.
    """
    #: Default class for context variables.
    context_class = Context
    #: URL adapter bound to a request.
    url_adapter = None
    #: Matched URL rule for a request.
    rule = None
    #: Keyword arguments from the matched rule.
    rule_args = None
    #: Exception raised when matching URL rules, if any.
    routing_exception = None

    def __init__(self, environ):
        """Initializes the request. This also sets a context attribute to
        hold variables valid for a single request.
        """
        super(WerkzeugRequest, self).__init__(environ)
        # Set up a context registry for this request.
        self.context = self.context_class()

    def url_for(self, endpoint, _full=False, _method=None, _anchor=None,
        **kwargs):
        """Builds and returns a URL for a named :class:`tipfy.Rule`.

        For example, if you have these rules registered in the application:

            Rule('/', endoint='home/main' handler='handlers.MyHomeHandler')
            Rule('/wiki', endoint='wiki/start' handler='handlers.WikiHandler')

        Here are some examples of how to generate URLs for them:

            >>> url = url_for('home/main')
            >>> '/'
            >>> url = url_for('home/main', _full=True)
            >>> 'http://localhost:8080/'
            >>> url = url_for('wiki/start')
            >>> '/wiki'
            >>> url = url_for('wiki/start', _full=True)
            >>> 'http://localhost:8080/wiki'
            >>> url = url_for('wiki/start', _full=True, _anchor='my-heading')
            >>> 'http://localhost:8080/wiki#my-heading'

        :param endpoint:
            The rule endpoint.
        :param _full:
            If True, returns an absolute URL. Otherwise, returns a relative
            one.
        :param _method:
            The rule request method, in case there are different rules
            for different request methods.
        :param _anchor:
            An anchor to add to the end of the URL.
        :param kwargs:
            Keyword arguments to build the URL.
        :return:
            An absolute or relative URL.
        """
        url = self.url_adapter.build(endpoint, force_external=_full,
            method=_method, values=kwargs)

        if _anchor:
            url += '#' + url_quote(_anchor)

        return url


class Response(WerkzeugResponse):
    """A response object with default mimetype set to 'text/html'."""
    default_mimetype = 'text/html'


class Tipfy(object):
    """The WSGI application which centralizes URL dispatching, configuration
    and hooks for an App Rngine app.
    """
    #: Default class for context variables.
    context_class = Context
    #: Default class for requests.
    request_class = Request
    #: Default class for responses.
    response_class = Response
    #: The active :class:`Tipfy` instance.
    app = None
    #: The active :class:`Request` instance.
    request = None

    def __init__(self, config=None):
        """Initializes the application.

        :param config:
            Dictionary with configuration for the application modules.
        """
        # Set the currently active wsgi app instance.
        self.set_wsgi_app()

        # Load default config and update with values for this instance.
        self.config = Config(config, {'tipfy': default_config})

        # Set up a context registry for this app.
        self.context = self.context_class()

        # Set a shortcut to the development flag.
        self.dev = self.config.get('tipfy', 'dev', False)

        # Set the url rules.
        self.url_map = self.config.get('tipfy', 'url_map')
        if not self.url_map:
            self.url_map = self.get_url_map()

        # Cache for loaded handler classes.
        self.handlers = {}

        # Middleware factory and registry.
        self.middleware_factory = MiddlewareFactory()

        # Store the app middleware dict.
        self.middleware = self.get_middleware(self, self.config.get('tipfy',
            'middleware'))

    def __call__(self, environ, start_response):
        """Shortcut for :meth:`wsgi_app`."""
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
            # Set the currently active wsgi app and request instances.
            request = self.request_class(environ)
            self.set_wsgi_app()
            self.set_request(request)

            # Make sure that the requested method is allowed in App Engine.
            if request.method.lower() not in ALLOWED_METHODS:
                raise MethodNotAllowed()

            # Match current URL and store routing exceptions if any.
            self.match_url(request)

            # Run pre_dispatch_handler middleware.
            rv = self.pre_dispatch(request)
            if rv is None:
                # Dispatch the requested handler.
                rv = self.dispatch(request)

            # Run post_dispatch_handler middleware.
            response = self.make_response(request, rv)
            response = self.post_dispatch(request, response)
        except RequestRedirect, e:
            # Execute redirects raised by the routing system or the
            # application.
            response = e
        except Exception, e:
            # Handle HTTP and uncaught exceptions.
            cleanup = not self.dev
            response = self.handle_exception(request, e)
            response = self.make_response(request, response)
        finally:
            # Do not clean local if we are in development mode and an
            # exception happened. This allows the debugger to still access
            # request and other variables from local in the interactive shell.
            if cleanup:
                self.cleanup()

        # Call the response object as a WSGI application.
        return response(environ, start_response)

    def match_url(self, request):
        """Matches registered URL rules against the request. This will store
        the URL adapter, matched rule and rule arguments in the request
        instance.

        Three exceptions can occur when matching the rules: :class:`NotFound`,
        :class:`MethodNotAllowed` or :class:`RequestRedirect`. If they are
        raised, they are stored in the request for later use.

        :param request:
            A :class:`Request` instance.
        :return:
            ``None``.
        """
        # Bind url map to the current request location.
        server_name = self.config.get('tipfy', 'server_name', None)
        subdomain = self.config.get('tipfy', 'subdomain', None)
        # Set self.url_adapter for backwards compatibility only.
        request.url_adapter = self.url_adapter = self.url_map.bind_to_environ(
            request.environ, server_name=server_name, subdomain=subdomain)

        # For backwards compatibility only.
        self.rule = self.rule_args = None

        try:
            # Match the path against registered rules.
            request.rule, request.rule_args = request.url_adapter.match(
                return_rule=True)
        except HTTPException, e:
            request.routing_exception = e

        # For backwards compatibility only.
        self.rule, self.rule_args = request.rule, request.rule_args

    def pre_dispatch(self, request):
        """Executes pre_dispatch_handler middleware. If a middleware returns
        anything, the chain is stopped and that value is retirned.

        :param request:
            A :class:`Request` instance.
        :return:
            The returned value from a middleware or `None`.
        """
        for hook in self.middleware.get('pre_dispatch_handler', []):
            rv = hook()
            if rv is not None:
                return rv

    def dispatch(self, request):
        """Matches the current URL against registered rules and returns the
        resut from the :class:`RequestHandler`.

        :param request:
            A :class:`Request` instance.
        :return:
            The returned value from a middleware or `None`.
        """
        if request.routing_exception is not None:
            raise request.routing_exception

        name = request.rule.handler
        if name not in self.handlers:
            # Import handler set in matched rule.
            self.handlers[name] = import_string(name)

        # Instantiate handler and dispatch request method.
        return self.handlers[name](self, request).dispatch()

    def post_dispatch(self, request, response):
        """Executes post_dispatch_handler middleware. All middleware are
        executed and must return a response object.

        :param request:
            A :class:`Request` instance.
        :param response:
            The :class:`Response` returned from :meth:`pre_dispatch` or
            :meth:`dispatch` and converted by :meth:`make_response`.
        :return:
            A :class:`Response` instance.
        """
        for hook in self.middleware.get('post_dispatch_handler', []):
            response = hook(response)

        return response

    def make_response(self, request, rv):
        """Converts the return value from a handler to a real response
        object that is an instance of :attr:`response_class`.

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

        This method comes from `Flask`_.

        :param request:
            A :class:`Request` instance.
        :param rv:
            The return value from the handler.
        :return:
            A :class:`Response` instance.
        """
        if rv is None:
            raise ValueError('Handler did not return a response.')

        if isinstance(rv, self.response_class):
            return rv

        if isinstance(rv, basestring):
            return self.response_class(rv)

        if isinstance(rv, tuple):
            return self.response_class(*rv)

        return self.response_class.force_type(rv, request.environ)

    def handle_exception(self, request, e):
        """Handles HTTPException or uncaught exceptions raised by the WSGI
        application, optionally applying exception middleware.

        :param request:
            A :class:`Request` instance.
        :param e:
            The catched exception.
        :return:
            A :class:`Response` instance, if the exception is not raised.
        """
        # Execute handle_exception middleware.
        for hook in self.middleware.get('handle_exception', []):
            response = hook(e)
            if response is not None:
                return response

        logging.exception(e)

        if self.dev:
            raise

        if isinstance(e, HTTPException):
            return e

        return InternalServerError()

    def get_middleware(self, obj, classes):
        """Returns a dictionary of all middleware instance methods for a given
        object.

        :param obj:
            The object to search for related middleware (the
            ``Tipfy`` or ``RequestHandler``).
        :param classes:
            A list of middleware classes.
        :return:
            A dictionary with middleware instance methods.
        """
        return self.middleware_factory.get_middleware(obj, classes)

    def get_config(self, module, key=None, default=DEFAULT_VALUE):
        """Returns a configuration value for a module. If it is not already
        set, loads a ``default_config`` variable from the given module,
        updates the app configuration with those default values and returns
        the value for the given key. If the key is still not available,
        returns the provided default value or raises an exception if no
        default was provided.

        Every `Tipfy`_ module that allows some kind of configuration sets a
        ``default_config`` global variable that is loaded by this function,
        cached and used in case the requested configuration was not defined
        by the user.

        :param module:
            The configured module.
        :param key:
            The config key.
        :return:
            A configuration value.
        """
        config = self.config
        value = config.get(module, key, DEFAULT_VALUE)
        if value not in (DEFAULT_VALUE, REQUIRED_VALUE):
            return value

        if default is DEFAULT_VALUE:
            # If no default was provided, the config is required.
            default = REQUIRED_VALUE

        if value is DEFAULT_VALUE:
            if module not in config.modules:
                # Update app config. If import fails or the default_config
                # attribute doesn't exist, an exception will be raised.
                config.setdefault(module, import_string(
                    module + ':default_config'))
                config.modules.append(module)

                value = config.get(module, key, default)
            else:
                value = default

        if value is REQUIRED_VALUE:
            raise KeyError('Module %s requires the config key "%s" to be '
                'set.' % (module, key))

        return value

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

    def set_wsgi_app(self):
        """Sets the currently active :class:`Tipfy` instance."""
        Tipfy.app = local.app = self

    def set_request(self, request):
        """Sets the currently active :class:`Request` instance.

        :param request:
            The currently active :class:`Request` instance.
        """
        Tipfy.request = local.request = request

    def cleanup(self):
        """Cleans :class:`Tipfy` variables at the end of a request."""
        Tipfy.app = Tipfy.request = None
        local.__release_local__()

    def get_test_client(self):
        """Creates a test client for this application.

        :return:
            A `werkzeug.Client`, which is a :class:`Tipfy` wrapped
            for tests.
        """
        from werkzeug import Client
        return Client(self, self.response_class, use_cookies=True)


class Config(dict):
    """A simple configuration dictionary keyed by module name. This is a
    dictionary of dictionaries. It requires all values to be dictionaries
    and applies updates and default values to the inner dictionaries instead of
    the first level one.
    """
    #: Loaded module configurations.
    modules = None

    def __init__(self, value=None, default=None):
        """Initializes the configuration object.

        :param value:
            A dictionary of configuration dictionaries for modules.
        :param default:
            A dictionary of configuration dictionaries for default values.
        """
        self.modules = []
        if value is not None:
            assert isinstance(value, dict)
            for module in value.keys():
                self.update(module, value[module])

        if default is not None:
            assert isinstance(default, dict)
            for module in default.keys():
                self.setdefault(module, default[module])

    def __setitem__(self, module, value):
        """Sets a configuration for a module, requiring it to be a dictionary.

        :param module:
            A module name for the configuration, e.g.: 'tipfy.ext.i18n'.
        :param value:
            A dictionary of configurations for the module.
        """
        assert isinstance(value, dict)
        super(Config, self).__setitem__(module, value)

    def update(self, module, value):
        """Updates the configuration dictionary for a module.

        >>> cfg = Config({'tipfy.ext.i18n': {'locale': 'pt_BR'})
        >>> cfg.get('tipfy.ext.i18n', 'locale')
        pt_BR
        >>> cfg.get('tipfy.ext.i18n', 'foo')
        None
        >>> cfg.update('tipfy.ext.i18n', {'locale': 'en_US', 'foo': 'bar'})
        >>> cfg.get('tipfy.ext.i18n', 'locale')
        en_US
        >>> cfg.get('tipfy.ext.i18n', 'foo')
        bar

        :param module:
            The module to update the configuration, e.g.: 'tipfy.ext.i18n'.
        :param value:
            A dictionary of configurations for the module.
        :return:
            None.
        """
        assert isinstance(value, dict)
        if module not in self:
            self[module] = {}

        self[module].update(value)

    def setdefault(self, module, value):
        """Sets a default configuration dictionary for a module.

        >>> cfg = Config({'tipfy.ext.i18n': {'locale': 'pt_BR'})
        >>> cfg.get('tipfy.ext.i18n', 'locale')
        pt_BR
        >>> cfg.get('tipfy.ext.i18n', 'foo')
        None
        >>> cfg.setdefault('tipfy.ext.i18n', {'locale': 'en_US', 'foo': 'bar'})
        >>> cfg.get('tipfy.ext.i18n', 'locale')
        pt_BR
        >>> cfg.get('tipfy.ext.i18n', 'foo')
        bar

        :param module:
            The module to set default configuration, e.g.: 'tipfy.ext.i18n'.
        :param value:
            A dictionary of configurations for the module.
        :return:
            None.
        """
        assert isinstance(value, dict)
        if module not in self:
            self[module] = {}

        for key in value.keys():
            self[module].setdefault(key, value[key])

    def get(self, module, key=None, default=None):
        """Returns a configuration value for given key in a given module.

        >>> cfg = Config({'tipfy.ext.i18n': {'locale': 'pt_BR'})
        >>> cfg.get('tipfy.ext.i18n')
        {'locale': 'pt_BR'}
        >>> cfg.get('tipfy.ext.i18n', 'locale')
        pt_BR
        >>> cfg.get('tipfy.ext.i18n', 'invalid-key')
        None
        >>> cfg.get('tipfy.ext.i18n', 'invalid-key', 'default-value')
        default-value

        :param module:
            The module to get a configuration from, e.g.: 'tipfy.ext.i18n'.
        :param key:
            The key from the module configuration.
        :param default:
            A default value to return in case the configuration for the
            module/key is not set.
        :return:
            The configuration value.
        """
        if module not in self:
            return default

        if key is None:
            return self[module]
        elif key not in self[module]:
            return default

        return self[module][key]


class MiddlewareFactory(object):
    """A factory and registry for middleware instances in use."""
    #: All middleware methods to look for.
    names = (
        'post_make_app',
        'pre_run_app',
        'pre_dispatch_handler',
        'post_dispatch_handler',
        'pre_dispatch',
        'post_dispatch',
        'handle_exception',
    )
    #: Methods that must run in reverse order.
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
            ``Tipfy`` or ``RequestHandler``).
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


def get_config(module, key=None, default=DEFAULT_VALUE):
    """Returns a configuration value for a module. If it is not already
    set, loads a ``default_config`` variable from the given module,
    updates the app configuration with those default values and returns
    the value for the given key. If the key is still not available,
    returns the provided default value or raises an exception if no
    default was provided.

    Every `Tipfy`_ module that allows some kind of configuration sets a
    ``default_config`` global variable that is loaded by this function,
    cached and used in case the requested configuration was not defined
    by the user.

    :param module:
        The configured module.
    :param key:
        The config key.
    :return:
        A configuration value.
    """
    return Tipfy.app.get_config(module, key, default)


def make_wsgi_app(config):
    """Returns a instance of :class:`Tipfy`.

    :param config:
        A dictionary of configuration values.
    :return:
        A :class:`Tipfy` instance.
    """
    app = Tipfy(config)

    if app.dev:
        logging.getLogger().setLevel(logging.DEBUG)

    # Execute post_make_app middleware.
    for hook in app.middleware.get('post_make_app', []):
        app = hook(app)

    return app


def run_wsgi_app(app):
    """Executes the application, optionally wrapping it by middleware.

    :param app:
        A :class:`Tipfy` instance.
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


__all__ = [
           'Config',
           'get_config',
           'make_wsgi_app',
           'Request',
           'RequestHandler',
           'run_wsgi_app',
           'Tipfy',
           'DEFAULT_VALUE',
           'REQUIRED_VALUE',]


# Old names.
WSGIApplication = Tipfy
REQUIRED_CONFIG = REQUIRED_VALUE
