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
    Request as BaseRequest, Response as BaseResponse, url_quote)
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
    # __import__('pkg_resources').declare_namespace(__name__)
    pass
except ImportError, e:
    pass

__version__ = '0.6.2'
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
default_config = {
    'apps_installed': [],
    'apps_entry_points': {},
    'middleware': [],
    'server_name': None,
    'subdomain': None,
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
            response = method(*args, **kwargs)

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

        .. seealso:: :meth:`Router.build`.
        """
        return self.app.router.build(self.request, _name, kwargs)


class Request(BaseRequest):
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

    def __init__(self, environ):
        """Initializes the request. This also sets a context attribute to
        hold variables valid for a single request.
        """
        super(Request, self).__init__(environ)
        # A registry for objects in use during a request.
        self.registry = {}
        # A context for template variables.
        self.context = {}

    def url_for(self, endpoint, **kwargs):
        """Builds and returns a URL for a named :class:`Rule`. This is here
        for backwards compatibility only. Use :meth:`Tipfy.url_for` or
        :meth:`RequestHandler.url_for` instead.

        This is a shortcut to :meth:`Tipfy.url_for`.
        """
        return Tipfy.app.url_for(endpoint, **kwargs)


class Response(BaseResponse):
    """A response object with default mimetype set to ``text/html``."""
    default_mimetype = 'text/html'


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
    )
    #: Methods that must run in reverse order.
    reverse_names = (
        'post_dispatch_handler',
        'post_dispatch',
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


class Router(object):
    def __init__(self, app, rules=None):
        """
        :param app:
            A :class:`Tipfy` instance.
        :param rules:
            Initial URL rules definitions. It can be a list of :class:`Rule`,
            a callable or a string defining a callable that returns the rules
            list. The callable is called passing the WSGI application as
            parameter. If None, it will import ``get_rules()`` from *urls.py*
            and call it passing the WSGI application.
        """
        self.app = app
        self.map = self.get_map(rules)
        # Cache for loaded handler classes.
        self.handlers = {}

    def add(self, rule):
        """Adds a rule to the URL map.

        :param path:
            The URL path.
        :param endpoint:
            The rule endpoint: an identifier for the rule.
        :param handler:
            A :class:`RequestHandler` class, or a module and class
            specification as a string.
        """
        self.map.add(rule)

    def match(self, request):
        """Matches registered :class:`Rule` definitions against the URL
        adapter. This will store the URL adapter, matched rule and rule
        arguments in the :class:`Request` instance.

        Three exceptions can occur when matching the rules: ``NotFound``,
        ``MethodNotAllowed`` or ``RequestRedirect``. If they are
        raised, they are stored in the request for later use.

        :param request:
            A :class:`Request` instance.
        :returns:
            None.
        """
        # Bind the URL map to the current request
        request.url_adapter = self.map.bind_to_environ(request.environ,
            server_name=self.app.config.get('tipfy', 'server_name'),
            subdomain=self.app.config.get('tipfy', 'subdomain'))

        # Match the path against registered rules.
        match = request.url_adapter.match(return_rule=True)
        request.rule, request.rule_args = match
        return match

    def dispatch_with_hooks(self, app, request, match):
        # XXX fix this method name, split in two: pre and post_dispatch.

        # Executes pre_dispatch_handler middleware. If a middleware returns
        # a response, the chain is stopped.
        for hook in app.middleware.get('pre_dispatch_handler', []):
            response = hook()
            if response is not None:
                break
        else:
            response = self.dispatch(app, request, match)

        # Executes post_dispatch_handler middleware. All middleware are
        # executed and must return a response object.
        for hook in app.middleware.get('post_dispatch_handler', []):
            response = hook(response)

        return response

    def dispatch(self, app, request, match, method=None):
        method = method or request.method.lower().replace('-', '_')
        rule, kwargs = match

        if isinstance(rule.handler, basestring):
            if rule.handler not in self.handlers:
                # Import handler set in matched rule. This can raise an
                # ImportError or AttributeError if the handler is badly
                # defined. The exception will be caught in the WSGI app.
                self.handlers[rule.handler] = import_string(rule.handler)

            rule.handler = self.handlers[rule.handler]

        # Instantiate handler.
        handler = rule.handler(app, request)
        try:
            # Dispatch the requested method.
            return handler(method, **kwargs)
        except Exception, e:
            if method == 'handle_exception':
                # We are already handling an exception.
                raise

            # If the handler implements exception handling, let it handle it.
            return handler.handle_exception(exception=e, debug=self.app.debug)

    def get_map(self, rules=None):
        """Returns a ``werkzeug.routing.Map`` instance with the given
        :class:`Rule` definitions.

        :param rules:
            A list of :class:`Rule`, a callable or a string defining
            a callable that returns the list of rules.
        :returns:
            A ``werkzeug.routing.Map`` instance.
        """
        if rules is None:
            # Load rules from urls.py.
            rules = 'urls.get_rules'

        if isinstance(rules, basestring):
            rules = import_string(rules, silent=True)
            if not rules:
                logging.warning('Missing %s. No URL rules were loaded.' %
                    rules)

        if callable(rules):
            rules = rules(self.app)

        return Map(rules)

    def build(self, request, name, kwargs):
        full = kwargs.pop('_full', False)
        method = kwargs.pop('_method', None)
        scheme = kwargs.pop('_scheme', None)
        netloc = kwargs.pop('_netloc', None)
        anchor = kwargs.pop('_anchor', None)

        if scheme or netloc:
            full = False

        url = request.url_adapter.build(name, values=kwargs, method=method,
            force_external=full)

        if scheme or netloc:
            scheme = scheme or 'http'
            netloc = netloc or request.host
            url = '%s://%s%s' % (scheme, netloc, url)

        if anchor:
            url += '#%s' % url_quote(anchor)

        return url


class Tipfy(object):
    """The WSGI application which centralizes URL dispatching, configuration
    and hooks for an App Rngine app.
    """
    #: Default class for requests.
    request_class = Request
    #: Default class for responses.
    response_class = Response
    #: Default class for the configuration object.
    config_class = Config
    #: Default class for the configuration object.
    router_class = Router
    #: The active :class:`Tipfy` instance.
    app = None
    #: The active :class:`Request` instance.
    request = None

    def __init__(self, config=None, rules=None, debug=False):
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
        Tipfy.app = self
        self.debug = debug
        self.registry = {}
        self.error_handlers = {}

        # Load default config and update with values for this instance.
        self.config = self.config_class(config, {'tipfy': default_config},
            ['tipfy'])

        # Middleware factory and registry.
        self.middleware_factory = MiddlewareFactory()

        # Store the app middleware dict.
        self.middleware = self.get_middleware(self, self.config.get('tipfy',
            'middleware'))

        self.router = self.router_class(self, rules)

    def __call__(self, environ, start_response):
        """Shortcut for :meth:`Tipfy.wsgi_app`."""
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        cleanup = True
        try:
            Tipfy.app = self
            Tipfy.request = request = self.request_class(environ)

            if request.method not in ALLOWED_METHODS:
                abort(501)

            match = self.router.match(request)
            response = self.router.dispatch_with_hooks(self, request, match)
        except Exception, e:
            try:
                response = self.handle_exception(request, e)
            except HTTPException, e:
                response = e
            except:
                if self.debug:
                    cleanup = False
                    raise

                response = InternalServerError()
        finally:
            if cleanup:
                Tipfy.app = Tipfy.request = None

        return response(environ, start_response)

    def handle_exception(self, request, exception):
        logging.exception(exception)

        if isinstance(exception, HTTPException):
            code = exception.code
        else:
            code = 500

        handler = self.error_handlers.get(code) or self.error_handlers.get(500)
        if handler:
            rule = Rule('/', handler=handler, endpoint='__exception__')
            kwargs = dict(exception=exception, debug=self.debug)
            return self.router.dispatch(self, request, (rule, kwargs),
                method='handle_exception')
        else:
            raise

    def get_config(self, module, key=None, default=REQUIRED_VALUE):
        """Returns a configuration value for a module.

        .. seealso:: :meth:`Config.get_or_load`.
        """
        return self.config.get_or_load(module, key=key, default=default)

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

    def url_for(self, _name, **kwargs):
        """Builds a URL for a named :class:`Rule`.

        .. seealso:: :meth:`Router.build`.
        """
        return self.router.build(self.request, _name, kwargs)

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

    @cached_property
    def dev(self):
        """True is the app is using the dev server, False otherwise."""
        return os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

    @cached_property
    def app_id(self):
        """The application ID as defined in *app.yaml*."""
        return os.environ.get('APPLICATION_ID', None)

    @cached_property
    def version_id(self):
        """The deployed version ID. Always '1' when using the dev server."""
        return os.environ.get('CURRENT_VERSION_ID', '1')


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


def url_for(endpoint, **kwargs):
    """Builds and returns a URL for a named :class:`Rule`.

    This is a shortcut to :meth:`Tipfy.url_for`.
    """
    # For backwards compatibility, check old keywords.
    if 'full' in kwargs:
        kwargs['_full'] = kwargs.pop('full')

    if 'method' in kwargs:
        kwargs['_method'] = kwargs.pop('method')

    return Tipfy.app.url_for(endpoint, **kwargs)


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

    if app.debug:
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