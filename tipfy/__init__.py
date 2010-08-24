# -*- coding: utf-8 -*-
"""
    tipfy
    ~~~~~

    Minimalist WSGI application and utilities for App Engine.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import logging
import os
from wsgiref.handlers import CGIHandler

# Werkzeug swiss knife.
# Need to import werkzeug first otherwise py_zipimport fails.
import werkzeug
from werkzeug import (cached_property, escape, import_string, redirect,
    Request as WerkzeugRequest, Response as WerkzeugResponse, url_quote)
from werkzeug.exceptions import (abort, BadGateway, BadRequest, Forbidden,
    Gone, HTTPException, InternalServerError, LengthRequired,
    MethodNotAllowed, NotAcceptable, NotFound, NotImplemented,
    PreconditionFailed, RequestEntityTooLarge, RequestTimeout,
    RequestURITooLarge, ServiceUnavailable, Unauthorized,
    UnsupportedMediaType)
from werkzeug.routing import (BaseConverter, EndpointPrefix, Map,
    RequestRedirect, Rule as WerkzeugRule, RuleFactory, RuleTemplate,
    Subdomain, Submount)

try:
    # We declare the namespace to be used outside of App Engine, so that
    # we can distribute and install separate extensions.
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError, e:
    pass

__version__ = '0.6.3'
__version_info__ = tuple(int(n) for n in __version__.split('.'))

#: Default configuration values for this module. Keys are:
#:
#: apps_installed
#:     A list of active app modules as a string. Default is an empty list.
#:
#: apps_entry_points
#:     URL entry points for the installed apps, in case their URLs are mounted
#:     using base paths.
#:
#: middleware
#:     A list of middleware classes for the WSGIApplication. The classes can
#:     be defined as strings. They define hooks that plug into the application
#:     to initialize stuff when the app is built, at the start or end of a
#:     request or to handle exceptions. Default is an empty list.
#:
#: server_name
#:     A server name hint, used to calculate current subdomain.
#:     If you plan to use dynamic subdomains, you must define the main domain
#:     here so that the subdomain can be extracted and applied to URL rules.
#:
#: subdomain
#:     Force this subdomain to be used instead of extracting
#:     the subdomain from the current url.
#:
#: dev
#:     True is this is the development server, False otherwise.
#:     Default is the value of ``os.environ['SERVER_SOFTWARE']``.
#:
#: app_id
#:     The application id. Default is the value of
#:     ``os.environ['APPLICATION_ID']``.
#:
#: version_id
#:     The current deplyment version id. Default is the value
#:     of ``os.environ['CURRENT_VERSION_ID']``.
default_config = {
    'apps_installed': [],
    'apps_entry_points': {},
    'middleware': [],
    'server_name': None,
    'subdomain': None,
    'dev': os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'),
    'app_id': os.environ.get('APPLICATION_ID', None),
    'version_id': os.environ.get('CURRENT_VERSION_ID', '1'),
}

# Allowed request methods.
ALLOWED_METHODS = frozenset(['DELETE', 'GET', 'HEAD', 'OPTIONS', 'POST', 'PUT',
    'TRACE'])
# Value used for required values.
REQUIRED_VALUE = object()
# Value used for missing default values.
DEFAULT_VALUE = object()


class RequestHandler(object):
    """Base class to handle requests. Implements the minimal interface
    required by :class:`Tipfy`.

    The dispatch method implements a middleware system to execute hooks before
    and after processing a request and to handle exceptions.
    """
    #: A list of middleware classes or callables. A middleware can implement
    #: three methods that are called before and after the current request
    #: method is executed, or if an exception occurs:
    #:
    #: pre_dispatch(handler)
    #:     Called before the requested method is
    #:     executed. If returns a response, stops the middleware chain and
    #:     uses that response, not calling the requested method.
    #:
    #: post_dispatch(handler, response)
    #:     Called after the requested method is executed. Must always return
    #:     a response. All *post_dispatch* middleware are always executed.
    #:
    #: handle_exception(exception, handler)
    #:     Called if an exception occurs.
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

    def __call__(self, _method, *args, **kwargs):
        """Executes a handler method. This is called by :class:`Tipfy` and
        must return a :class:`Response` object.

        :param _method:
            The method to be dispatched, normally the request method in
            lower case, e.g., 'get', 'post', 'head' or 'put'.
        :param kwargs:
            Keyword arguments from the matched :class:`Rule`.
        :return:
            A :class:`Response` instance.
        """
        method = getattr(self, _method, None)
        if method is None:
            # 405 Method Not Allowed.
            # The response MUST include an Allow header containing a
            # list of valid methods for the requested resource.
            # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.6
            self.abort(405, valid_methods=get_valid_methods(self))

        if not self.middleware:
            # No middleware is set: just execute the method.
            return method(*args, **kwargs)

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
                response = method(*args, **kwargs)
            except Exception, e:
                # Execute handle_exception middleware.
                for hook in middleware.get('handle_exception', []):
                    response = hook(e, self)
                    if response is not None:
                        break
                else:
                    raise

        # Make sure we have a response object.
        response = self.app.make_response(self.request, response)

        # Execute post_dispatch middleware.
        for hook in middleware.get('post_dispatch', []):
            response = hook(self, response)

        # Done!
        return response

    def dispatch(self, _method, *args, **kwargs):
        """Deprecated method: a wrapper for :meth:`__call__`."""
        return self(_method, *args, **kwargs)

    def abort(self, code, *args, **kwargs):
        """Raises an :class:`HTTPException`. This stops code execution,
        leaving the HTTP exception to be handled by an exception handler.

        :param code:
            HTTP status error code (e.g., 404).
        :param args:
            Positional arguments to be passed to the exception class.
        :param kwargs:
            Keyword arguments to be passed to the exception class.
        """
        abort(code, *args, **kwargs)

    def get_config(self, module, key=None, default=REQUIRED_VALUE):
        """Returns a configuration value for a module.

        .. seealso:: :meth:`Config.get_or_load`.
        """
        return self.app.config.get_or_load(module, key=key, default=default)

    def handle_exception(self, exception=None, debug=False):
        """Handles an exception. The default behavior is to re-raise the
        exception (no exception handling is implemented).

        :param exception:
            The exception that was thrown.
        :param debug:
            True if the exception should be handled in debug mode.
        """
        raise

    def redirect(self, location, code=302):
        """Issues an HTTP redirect to the given URL. This won't stop
        code execution. You must return when calling this method::

            return self.redirect('/some-path')

        :param location:
            An absolute URI.
        :param code:
            The HTTP status code for the redirect.
        :return:
            A :class:`Response` object with headers set for redirection.
        """
        return redirect(location, code)

    def redirect_to(self, _name, _code=302, **kwargs):
        """Convenience method mixing :meth:`redirect` and :methd:`url_for`:
        redirects the client to a URL built using a named :class:`Rule`.

        :param _name:
            The rule name.
        :param _code:
            The HTTP status code for the redirect.
        :param kwargs:
            Keyword arguments to build the URL.
        :return:
            A :class:`Response` object with headers set for redirection.
        """
        return self.redirect(self.url_for(_name, **kwargs), code=_code)

    def url_for(self, _name, **kwargs):
        """Builds a URL for a named :class:`Rule`.

        .. seealso:: :meth:`Request.url_for`.
        """
        return self.request.url_for(_name, **kwargs)


class Request(WerkzeugRequest):
    """The :class:`Request` object contains all environment variables for the
    current request: GET, POST, FILES, cookies and headers. Additionally
    it stores the URL adapter bound to the request and information about the
    matched URL rule.
    """
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
        super(Request, self).__init__(environ)

        # A registry for objects in use during a request.
        self.registry = {}

        # A context for template variables.
        self.context = {}

    def url_for(self, endpoint, _full=False, _method=None, _anchor=None,
        **kwargs):
        """Builds and returns a URL for a named :class:`Rule`.

        For example, if you have these rules registered in the application:

        .. code-block::

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
            If True, returns an absolute URL. Otherwise, returns a
            relative one.
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
    """A response object with default mimetype set to ``text/html``."""
    default_mimetype = 'text/html'


class Tipfy(object):
    """The WSGI application which centralizes URL dispatching, configuration
    and hooks for an App Rngine app.
    """
    #: Default class for requests.
    request_class = Request
    #: Default class for responses.
    response_class = Response
    #: The active :class:`Tipfy` instance.
    app = None
    #: The active :class:`Request` instance.
    request = None

    def __init__(self, config=None, rules='urls.get_rules', debug=False):
        """Initializes the application.

        :param config:
            Dictionary with configuration for the application modules.
        :param rules:
            URL rules definitions for the application. It can be a list of
            :class:`Rule`, a callable or a string defining a callable that
            returns the rules list. The callable is called passing the WSGI
            application as parameter. Default is ``urls.get_rules``: import
            ``get_rules()`` from *urls.py* and calls it passing the app.
        """
        # Set the currently active wsgi app instance.
        self.set_wsgi_app()

        # Load default config and update with values for this instance.
        self.config = Config(config, {'tipfy': default_config}, ['tipfy'])

        # Set up a context registry for this app.
        self.registry = {}

        # Set a shortcut to the development flag.
        self.dev = self.config.get('tipfy', 'dev', False)

        # Cache for loaded handler classes.
        self.handlers = {}

        # Middleware factory and registry.
        self.middleware_factory = MiddlewareFactory()

        # Store the app middleware dict.
        self.middleware = self.get_middleware(self, self.config.get('tipfy',
            'middleware'))

        # Initialize the URL map.
        self.url_map = self.get_url_map(rules)

    def __call__(self, environ, start_response):
        """Shortcut for :meth:`Tipfy.wsgi_app`."""
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        """The actual WSGI application.  This is not implemented in
        :meth:`Tipfy.__call__` so that middlewares can be applied without
        losing a reference to the class. So instead of doing this::

            app = MyMiddleware(app)

        It's a better idea to do this instead::

            app.wsgi_app = MyMiddleware(app.wsgi_app)

        Then you still have the original application object around and
        can continue to call methods on it.

        :param environ:
            A WSGI environment.
        :param start_response:
            A callable accepting a status code, a list of headers and an
            optional exception context to start the response.
        """
        cleanup = True
        try:
            # Set the currently active wsgi app and request instances.
            request = self.request_class(environ)
            self.set_wsgi_app()
            self.set_request(request)

            # Make sure that the requested method is allowed in App Engine.
            if request.method not in ALLOWED_METHODS:
                abort(501)

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
            # Do not clean request if we are in development mode and an
            # exception happened. This allows the debugger to still access
            # request and other variables in the interactive shell.
            if cleanup:
                self.cleanup()

        # Call the response object as a WSGI application.
        return response(environ, start_response)

    def get_url_map(self, rules=None):
        """Returns a ``werkzeug.routing.Map`` instance with initial
        :class:`Rule` definitions.

        :param rules:
            Initial list of :class:`Rule`, a callable or a string defining
            a callable that returns the list of rules.
        :return:
            A ``werkzeug.routing.Map`` instance.
        """
        if isinstance(rules, basestring):
            try:
                rules = import_string(rules)
            except (AttributeError, ImportError), e:
                logging.warning('Missing %s. No URL rules were loaded.' %
                    rules)
                rules = None

        if callable(rules):
            try:
                rules = rules(self)
            except TypeError, e:
                # Backwards compatibility:
                # Previously get_rules() didn't receive the WSGI app.
                rules = rules()

        return Map(rules)

    def add_url_rule(self, path, endpoint, handler, **kwargs):
        """Adds a rule to the URL map.

        :param path:
            The URL path.
        :param endpoint:
            The rule endpoint: an identifier for the rule.
        :param handler:
            A :class:`RequestHandler` class, or a module and class
            specification as a string.
        """
        rule = Rule(path, endpoint=endpoint, handler=handler, **kwargs)
        self.url_map.add(rule)

    def match_url(self, request):
        """Matches registered :class:`Rule` definitions against the request.
        This will store the URL adapter, matched rule and rule arguments in
        the :class: `Request` instance.

        Three exceptions can occur when matching the rules: ``NotFound``,
        ``MethodNotAllowed`` or ``RequestRedirect``. If they are
        raised, they are stored in the request for later use.

        :param request:
            A :class:`Request` instance.
        :return:
            None.
        """
        # Bind url map to the current request location.
        config = self.config.get('tipfy')
        request.url_adapter = self.url_map.bind_to_environ(request.environ,
            server_name=config.get('server_name'),
            subdomain=config.get('subdomain'))

        try:
            # Match the path against registered rules.
            request.rule, request.rule_args = request.url_adapter.match(
                return_rule=True)
        except HTTPException, e:
            request.routing_exception = e

    def pre_dispatch(self, request):
        """Executes pre_dispatch_handler middleware. If a middleware returns
        anything, the chain is stopped and that value is retirned.

        :param request:
            A :class:`Request` instance.
        :return:
            The returned value from a middleware or None.
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
            The returned value from a middleware or None.
        """
        if request.routing_exception is not None:
            raise request.routing_exception

        handler = request.rule.handler
        if isinstance(handler, basestring):
            if handler not in self.handlers:
                # Import handler set in matched rule.
                self.handlers[handler] = import_string(handler)

            handler = self.handlers[handler]

        # Instantiate handler and dispatch requested method.
        method = request.method.lower().replace('-', '_')
        return handler(self, request)(method, **request.rule_args)

    def post_dispatch(self, request, response):
        """Executes post_dispatch_handler middleware. All middleware are
        executed and must return a response object.

        :param request:
            A :class:`Request` instance.
        :param response:
            The :class:`Response` returned from :meth:`Tipfy.pre_dispatch`
            or :meth:`Tipfy.dispatch` and converted by
            :meth:`Tipfy.make_response`.
        :return:
            A :class:`Response` instance.
        """
        for hook in self.middleware.get('post_dispatch_handler', []):
            response = hook(response)

        return response

    def make_response(self, request, rv):
        """Converts the return value from a handler to a real response
        object that is an instance of :class:`Response`.

        The following types are allowd for ``rv``:

        response_class
            The object is returned unchanged.

        str
            A response object is created with the string as body.

        unicode
            A response object is created with the string encoded to
            utf-8 as body.

        tuple
            The response object is created with the contents of the
            tuple as arguments.

        WSGI function
            The function is called as WSGI application and
            buffered as response object.

        This method comes from `Flask <http://flask.pocoo.org/>`_.

        :param request:
            A :class:`Request` instance.
        :param rv:
            The return value from the handler.
        :return:
            A :class:`Response` instance.
        """
        if isinstance(rv, self.response_class):
            return rv

        if isinstance(rv, basestring):
            return self.response_class(rv)

        if isinstance(rv, tuple):
            return self.response_class(*rv)

        if rv is None:
            raise ValueError('Handler did not return a response.')

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

        if self.dev:
            raise

        logging.exception(e)

        if isinstance(e, HTTPException):
            return e

        return InternalServerError()

    def get_middleware(self, obj, classes):
        """Returns a dictionary of all middleware instance methods for a given
        object.

        :param obj:
            The object to search for related middleware (:class:`Tipfy` or
            :class:`RequestHandler` instance).
        :param classes:
            A list of middleware classes.
        :return:
            A dictionary with middleware instance methods.
        """
        if not classes:
            return {}

        return self.middleware_factory.get_middleware(obj, classes)

    def get_config(self, module, key=None, default=REQUIRED_VALUE):
        """Returns a configuration value for a module.

        .. seealso:: :meth:`Config.get_or_load`.
        """
        return self.config.get_or_load(module, key=key, default=default)

    def set_wsgi_app(self):
        """Sets the currently active :class:`Tipfy` instance."""
        Tipfy.app = self

    def set_request(self, request):
        """Sets the currently active :class:`Request` instance.

        :param request:
            The currently active :class:`Request` instance.
        """
        Tipfy.request = request

    def cleanup(self):
        """Cleans :class:`Tipfy` variables at the end of a request."""
        Tipfy.app = Tipfy.request = None

    def get_test_client(self):
        """Creates a test client for this application.

        :return:
            A ``werkzeug.Client``, which is a :class:`Tipfy` wrapped
            for tests.
        """
        from werkzeug import Client
        return Client(self, self.response_class, use_cookies=True)

    def run(self):
        """Runs the app using ``CGIHandler``. This must be called inside a
        ``main()`` function in the file defined in *app.yaml* to run the
        application::

            # ...

            app = Tipfy(rules=[
                Rule('/', endpoint='home', handler=HelloWorldHandler),
            ])

            def main():
                app.run()

            if __name__ == '__main__':
                main()
        """
        # Fix issue #772.
        if self.dev:
            fix_sys_path()

        CGIHandler().run(self)


class Config(dict):
    """A simple configuration dictionary keyed by module name. This is a
    dictionary of dictionaries. It requires all values to be dictionaries
    and applies updates and default values to the inner dictionaries instead
    of the first level one.

    The configuration object is available as a ``config`` attribute of
    :class:`Tipfy`. If is instantiated and populated when the app is built::

        config = {}

        config['my.module'] = {
            'foo': 'bar',
        }

        app = Tipfy(rules=[Rule('/', endpoint='home', handler=MyHandler)], config=config)

    Then to read configuration values, use :meth:`RequestHandler.get_config`::

        class MyHandler(RequestHandler):
            def get(self):
                foo = self.get_config('my.module', 'foo')

                # ...
    """
    #: Loaded module configurations.
    loaded = None

    def __init__(self, value=None, default=None, loaded=None):
        """Initializes the configuration object.

        :param value:
            A dictionary of configuration dictionaries for modules.
        :param default:
            A dictionary of configuration dictionaries for default values.
        :param loaded:
            A list of modules to be marked as loaded.
        """
        self.loaded = loaded or []
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
            A module name for the configuration, e.g.: `tipfy.ext.i18n`.
        :param value:
            A dictionary of configurations for the module.
        """
        assert isinstance(value, dict)
        super(Config, self).__setitem__(module, value)

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
            The module to get a configuration from, e.g.: `tipfy.ext.i18n`.
        :param key:
            The key from the module configuration.
        :param default:
            A default value to return when the configuration for the given
            key is not set. It is only returned if **key** is defined.
        :returns:
            The configuration value.
        """
        if module not in self:
            if key is None:
                return None

            return default

        if key is None:
            return self[module]

        if key not in self[module]:
            return default

        return self[module][key]

    def get_or_load(self, module, key=None, default=REQUIRED_VALUE):
        """Returns a configuration value for a module. If it is not already
        set, loads a ``default_config`` variable from the given module,
        updates the app configuration with those default values and returns
        the value for the given key. If the key is still not available,
        returns the provided default value or raises an exception if no
        default was provided.

        Every module that allows some kind of configuration sets a
        ``default_config`` global variable that is loaded by this function,
        cached and used in case the requested configuration was not defined
        by the user.

        :param module:
            The configured module.
        :param key:
            The config key.
        :param default:
            A default value to return in case the configuration for
            the module/key is not set.
        :returns:
            A configuration value.
        """
        if module not in self.loaded:
            # Load default configuration and update config.
            values = import_string(module + '.default_config', silent=True)
            if values:
                self.setdefault(module, values)

            self.loaded.append(module)

        value = self.get(module, key, default)

        if value is not REQUIRED_VALUE and not (key is None and value is None):
            return value

        if key is None and value is None:
            raise KeyError('Module %s is not configured.' % module)

        raise KeyError('Module %s requires the config key "%s" to be '
                'set.' % (module, key))

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
            The module to set default configuration, e.g.: `tipfy.ext.i18n`.
        :param value:
            A dictionary of configurations for the module.
        :returns:
            None.
        """
        assert isinstance(value, dict)
        if module not in self:
            self[module] = {}

        for key in value.keys():
            self[module].setdefault(key, value[key])

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
            The module to update the configuration, e.g.: `tipfy.ext.i18n`.
        :param value:
            A dictionary of configurations for the module.
        :returns:
            None.
        """
        assert isinstance(value, dict)
        if module not in self:
            self[module] = {}

        self[module].update(value)


class MiddlewareFactory(object):
    """A factory and registry for middleware instances in use."""
    #: All middleware methods to look for.
    names = (
        'post_make_app',
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
            The object to search for related middleware (the :class:`Tipfy` or
            :class:`RequestHandler`).
        :param classes:
            A list of middleware classes.
        :return:
            A dictionary with middleware instance methods.
        """
        id = obj.__module__ + '.' + obj.__class__.__name__

        if id not in self.obj_middleware:
            self.obj_middleware[id] = self.load_middleware(classes)

        return self.obj_middleware[id]

    def load_middleware(self, specs):
        """Returns a dictionary of middleware instance methods for a list of
        middleware specifications.

        :param specs:
            A list of middleware classes, classes as strings or instances.
        :return:
            A dictionary with middleware instance methods.
        """
        res = {}

        for spec in specs:
            # Middleware can be defined in 3 forms: strings, classes and
            # instances.
            is_str = isinstance(spec, basestring)
            is_obj = not is_str and not isinstance(spec, type)

            if is_obj:
                # Instance.
                spec_id = id(spec)
                obj = spec
            elif is_str:
                spec_id = spec
            else:
                spec_id = spec.__module__ + '.' + spec.__name__

            if spec_id not in self.methods:
                if is_str:
                    spec = import_string(spec, silent=True)
                    if not spec:
                        logging.warning('Missing %s. Middleware was not '
                            'loaded.' % spec)
                        continue

                if not is_obj:
                    obj = spec()

                self.instances[spec_id] = obj
                self.methods[spec_id] = [getattr(obj, n, None) for n in \
                    self.names]

            for name, method in zip(self.names, self.methods[spec_id]):
                if method:
                    res.setdefault(name, []).append(method)

        for name in self.reverse_names:
            if name in res:
                res[name].reverse()

        return res


class Rule(WerkzeugRule):
    """Extends Werkzeug routing to support a handler definition for each Rule.
    Handler is a :class:`RequestHandler` module and class specification, and
    endpoint is a friendly name used to build URL's. For example:

    .. code-block:: python

        Rule('/users', endpoint='user-list', handler='my_app:UsersHandler')

    Access to the URL ``/users`` loads ``UsersHandler`` class from
    ``my_app`` module. To generate a URL to that page, use :func:`url_for`::

        url = url_for('user-list')
    """
    def __init__(self, *args, **kwargs):
        self.handler = kwargs.pop('handler', kwargs.get('endpoint', None))
        super(Rule, self).__init__(*args, **kwargs)

    def empty(self):
        """Returns an unbound copy of this rule. This can be useful if you
        want to reuse an already bound URL for another map.
        """
        defaults = None
        if self.defaults is not None:
            defaults = dict(self.defaults)
        return Rule(self.rule, defaults, self.subdomain, self.methods,
                    self.build_only, self.endpoint, self.strict_slashes,
                    self.redirect_to, handler=self.handler)


class HandlerPrefix(RuleFactory):
    """Prefixes all handler values (which must be strings for this factory) of
    nested rules with another string. For example, take these rules::

        rules = [
            HandlerPrefix('my_app.handlers.', [
                Rule('/', endpoint='index', handler='IndexHandler'),
                Rule('/entry/<entry_slug>', endpoint='show', handler='ShowHandler'),
            ]),
        ]

    These are the same as::

        rules = [
            Rule('/', endpoint='index', handler='my_app.handlers.IndexHandler'),
            Rule('/entry/<entry_slug>', endpoint='show', handler='my_app.handlers.ShowHandler'),
        ]
    """
    def __init__(self, prefix, rules):
        self.prefix = prefix
        self.rules = rules

    def get_rules(self, map):
        for rulefactory in self.rules:
            for rule in rulefactory.get_rules(map):
                rule = rule.empty()
                rule.handler = self.prefix + rule.handler
                yield rule


def get_config(module, key=None, default=REQUIRED_VALUE):
    """Returns a configuration value for a module.

    .. seealso:: :meth:`Config.get_or_load`.
    """
    return Tipfy.app.config.get_or_load(module, key=key, default=default)


def get_valid_methods(handler):
    """Returns a list of HTTP methods supported by a handler.

    :param handler:
        A :class:`RequestHandler` instance.
    :returns:
        A list of HTTP methods supported by the handler.
    """
    return [method for method in ALLOWED_METHODS if
        getattr(handler, method.lower().replace('-', '_'), None)]


def url_for(endpoint, _full=False, _method=None, _anchor=None, **kwargs):
    """Builds and returns a URL for a named :class:`Rule`.

    This is a shortcut to :meth:`Request.url_for`.
    """
    # For backwards compatibility, check old keywords.
    full = kwargs.pop('full', _full)
    method = kwargs.pop('method', _method)

    return Tipfy.request.url_for(endpoint, _full=full, _method=method,
        _anchor=_anchor, **kwargs)


def redirect_to(endpoint, _method=None, _anchor=None, _code=302, **kwargs):
    """Convenience function mixing ``werkzeug.redirect`` and
    :meth:`Request.url_for`: redirects the client to a URL built using a named
    :class:`Rule`.

    :param endpoint:
        The rule endpoint.
    :param _method:
        The rule request method, in case there are different rules
        for different request methods.
    :param _anchor:
        An anchor to add to the end of the URL.
    :param _code:
        The redirect status code.
    :param kwargs:
        Keyword arguments to build the URL.
    :return:
        A :class:`Response` object with headers set for redirection.
    """
    # For backwards compatibility, check old keywords.
    method = kwargs.pop('method', _method)
    code = kwargs.pop('code', _code)

    url = Tipfy.request.url_for(endpoint, _full=True, _method=method,
        _anchor=_anchor, **kwargs)
    return redirect(url, code=code)


def render_json_response(*args, **kwargs):
    """Renders a JSON response.

    :param args:
        Arguments to be passed to simplejson.dumps().
    :param kwargs:
        Keyword arguments to be passed to simplejson.dumps().
    :return:
        A :class:`Response` object with a JSON string in the body and
        mimetype set to ``application/json``.
    """
    from django.utils import simplejson
    return Response(simplejson.dumps(*args, **kwargs),
        mimetype='application/json')


def make_wsgi_app(config=None, **kwargs):
    """Returns a instance of :class:`Tipfy`.

    :param config:
        A dictionary of configuration values.
    :param kwargs:
        Additional keyword arguments to instantiate :class:`Tipfy`.
    :return:
        A :class:`Tipfy` instance.
    """
    app = Tipfy(config=config, **kwargs)

    if app.dev:
        logging.getLogger().setLevel(logging.DEBUG)

    # Execute post_make_app middleware.
    for hook in app.middleware.get('post_make_app', []):
        app = hook(app)

    return app


def run_wsgi_app(app):
    """Executes the application, optionally wrapping it by middleware.

    .. warning::
       This is deprecated. Use app.run() instead.

    :param app:
        A :class:`Tipfy` instance.
    :return:
        None.
    """
    app.run()


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
    'DEFAULT_VALUE',
    'EndpointPrefix',
    'HTTPException',
    'InternalServerError',
    'Map',
    'REQUIRED_VALUE',
    'Request',
    'RequestHandler',
    'RequestRedirect',
    'Response',
    'Rule',
    'RuleTemplate',
    'Subdomain',
    'Submount',
    'Tipfy',
    'abort',
    'cached_property',
    'default_config',
    'escape',
    'get_config',
    'import_string',
    'make_wsgi_app',
    'redirect',
    'redirect_to',
    'render_json_response',
    'run_wsgi_app',
    'url_for',
    'url_quote',
]