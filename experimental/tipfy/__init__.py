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
import urlparse
from wsgiref.handlers import CGIHandler

# Werkzeug Swiss knife.
# Need to import werkzeug first otherwise py_zipimport fails.
import werkzeug
from werkzeug import (Request as BaseRequest, Response as BaseResponse,
    cached_property, import_string, redirect as base_redirect, url_quote)
from werkzeug.exceptions import HTTPException, InternalServerError, abort
from werkzeug.routing import BaseConverter, Map, Rule as BaseRule, RuleFactory

from tipfy.utils import json_encode

__version__ = '0.7'
__version_info__ = tuple(int(n) for n in __version__.split('.'))

#: Default configuration values for this module. Keys are:
#:
#: server_name
#:     The server name used to calculate current subdomain. If you want to use
#:     dynamic subdomains, define the main domain here so that the subdomain
#:     can be calculated to match URL rules.
#:
#: default_subdomain
#:     The default subdomain used for rules without a subdomain defined.
default_config = {
    'server_name': None,
    'default_subdomain': '',
}

# Allowed request methods.
ALLOWED_METHODS = frozenset(['DELETE', 'GET', 'HEAD', 'OPTIONS', 'POST', 'PUT',
    'TRACE'])
# Value used for required values.
REQUIRED_VALUE = object()
# Value used for missing default values.
DEFAULT_VALUE = object()
# App Engine flags
DEV = os.environ.get('SERVER_SOFTWARE', '') == 'Development/1.0'
APP_ID = os.environ.get('APPLICATION_ID', None)
VERSION_ID = os.environ.get('CURRENT_VERSION_ID', '1')
IS_APPENGINE = (APP_ID and VERSION_ID)


class RequestHandler(object):
    """Base class to handle requests. Implements the minimal interface
    required by :class:`Tipfy`.

    The dispatch method implements a middleware system to execute hooks before
    and after processing a request and to handle exceptions.
    """
    #: A list of plugin classes or callables. A plugin can implement
    #: three methods that are called before and after the current request
    #: method is executed, or if an exception occurs:
    #:
    #: before_dispatch(handler)
    #:     Called before the requested method is
    #:     executed. If returns a response, stops the plugin chain and
    #:     uses that response, not calling the requested method.
    #:
    #: after_dispatch(handler, response)
    #:     Called after the requested method is executed. Must always return
    #:     a response. All *post_dispatch* plugin are always executed.
    #:
    #: handle_exception(handler, exception, debug)
    #:     Called if an exception occurs while executing the requested method.
    plugins = None

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
        :returns:
            A :class:`Response` instance.
        """
        method = getattr(self, _method, None)
        if method is None:
            # 405 Method Not Allowed.
            # The response MUST include an Allow header containing a
            # list of valid methods for the requested resource.
            # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.6
            self.abort(405, valid_methods=get_valid_methods(self))

        if not self.plugins:
            # No plugins are set: just execute the method.
            return method(*args, **kwargs)

        # Execute before_dispatch plugins.
        for plugin in self.plugins:
            func = getattr(plugin, 'before_dispatch', None)
            if func:
                response = func(self)
                if response is not None:
                    break
        else:
            try:
                response = method(*args, **kwargs)
            except Exception, e:
                # Execute handle_exception plugins.
                for plugin in reversed(self.plugins):
                    func = getattr(plugin, 'handle_exception', None)
                    if func:
                        response = func(self, e, self.app.debug)
                        if response is not None:
                            break

        # Execute after_dispatch plugins.
        for plugin in reversed(self.plugins):
            func = getattr(plugin, 'after_dispatch', None)
            if func:
                response = func(self, response)

        # Done!
        return response

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
        """Returns a response object with headers set for redirection to the
        given URI. This won't stop code execution, so you must return when
        calling this method::

            return self.redirect('/some-path')

        :param location:
            A relative or absolute URI (e.g., '../contacts').
        :param code:
            The HTTP status code for the redirect.
        :returns:
            A :class:`Response` object with headers set for redirection.
        """
        if not location.startswith('http'):
            # Make it absolute.
            location = urlparse.urljoin(self.request.url, location)

        return redirect(location, code)

    def redirect_to(self, _name, _code=302, **kwargs):
        """Convenience method mixing :meth:`redirect` and :methd:`url_for`:
        returns a response object with headers set for redirection to a URL
        built using a named :class:`Rule`.

        :param _name:
            The rule name.
        :param _code:
            The HTTP status code for the redirect.
        :param kwargs:
            Keyword arguments to build the URL.
        :returns:
            A :class:`Response` object with headers set for redirection.
        """
        return self.redirect(self.url_for(_name, **kwargs), code=_code)

    def url_for(self, _name, **kwargs):
        """Returns a URL for a named :class:`Rule`.

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

        app = Tipfy(rules=[Rule('/', name='home', handler=MyHandler)], config=config)

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


class Rule(BaseRule):
    """Extends Werkzeug routing to support handler and name definitions for
    each Rule. Handler is a :class:`RequestHandler` class and name is a
    friendly name used to build URL's. For example:

    .. code-block:: python

        Rule('/users', name='user-list', handler='my_app:UsersHandler')

    Access to the URL ``/users`` loads ``UsersHandler`` class from
    ``my_app`` module. To generate a URL to that page, use :func:`url_for`::

        url = url_for('user-list')
    """
    def __init__(self, path, handler=None, name=None, **kwargs):
        self.name = kwargs.pop('endpoint', name)
        self.handler = handler or self.name
        super(Rule, self).__init__(path, endpoint=self.name, **kwargs)

    def empty(self):
        """Returns an unbound copy of this rule. This can be useful if you
        want to reuse an already bound URL for another map.
        """
        defaults = None
        if self.defaults is not None:
            defaults = dict(self.defaults)

        return Rule(self.rule, handler=self.handler, name=self.endpoint,
            defaults=defaults, subdomain=self.subdomain, methods=self.methods,
            build_only=self.build_only, strict_slashes=self.strict_slashes,
            redirect_to=self.redirect_to)


class HandlerPrefix(RuleFactory):
    """Prefixes all handler values (which must be strings for this factory) of
    nested rules with another string. For example, take these rules::

        rules = [
            Rule('/', name='index', handler='my_app.handlers.IndexHandler'),
            Rule('/entry/<entry_slug>', name='show', handler='my_app.handlers.ShowHandler'),
        ]

    You can wrap them by ``HandlerPrefix`` to define the handler module and
    avoid repetition. This is equivalent to the above::

        rules = [
            HandlerPrefix('my_app.handlers.', [
                Rule('/', name='index', handler='IndexHandler'),
                Rule('/entry/<entry_slug>', name='show', handler='ShowHandler'),
            ]),
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


class RegexConverter(BaseConverter):
    """A :class: `Rule` converter that matches a regular expression::

        Rule(r'/<regex(".*$"):name>')
    """
    def __init__(self, map, *items):
        BaseConverter.__init__(self, map)
        self.regex = items[0]


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
        self.handlers = {}
        self.map = self.get_map(rules)

    def add(self, rule):
        """Adds a rule to the URL map.

        :param rule:
            A :class:`Rule` or rule factory to be added.
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
            server_name=self.get_server_name())

        # Match the path against registered rules.
        match = request.url_adapter.match(return_rule=True)
        request.rule, request.rule_args = match
        return match

    def dispatch(self, app, request, match, method=None):
        """Dispatches a request. This calls the :class:`RequestHandler` from
        the matched :class:`Rule`.

        :param app:
            A :class:`Tipfy` instance.
        :param request:
            A :class:`Request` instance.
        :param match:
            A tuple ``(rule, kwargs)``, resulted from the matched URL.
        :param method:
            Handler method to be called. In cases like exception handling, a
            method can be forced instead of using the request method.
        """
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

    def build(self, request, name, kwargs):
        """Returns a URL for a named :class:`Rule`. This is the central place
        to build URLs for an app. It is used by :meth:`RequestHandler.url_for`,
        :meth:`Tipfy.url_for and the standalone function :func:`url_for`.
        Those functions conveniently pass the current request object so you
        don't have to.

        :param request:
            The current request object.
        :param name:
            The rule name.
        :param kwargs:
            Values to build the URL. All variables not set in the rule
            default values must be passed and must conform to the format set
            in the rule. Extra keywords are appended as query arguments.

            A few keywords have special meaning:

            - **_full**: If True, builds an absolute URL.
            - **_method**: Uses a rule defined to handle specific request
              methods, if any are defined.
            - **_scheme**: URL scheme, e.g., `http` or `https`. If defined,
              an absolute URL is always returned.
            - **_netloc**: Network location, e.g., `www.google.com`. If
              defined, an absolute URL is always returned.
            - **_anchor**: If set, appends an anchor to generated URL.
        :returns:
            An absolute or relative URL.
        """
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
            url = '%s://%s%s' % (scheme or 'http', netloc or request.host, url)

        if anchor:
            url += '#%s' % url_quote(anchor)

        return url

    def get_server_name(self):
        """Returns the server name used to bind the URL map. By default it
        returns the configured server name. Extend this if you want to
        calculate the server name dynamically (e.g., to match subdomains
        from multiple domains).

        :returns:
            The server name used to build the URL adapter.
        """
        return self.app.config.get('tipfy', 'server_name')

    def get_default_subdomain(self):
        """Returns the default subdomain for rules without a subdomain
        defined. By default it returns the configured default subdomain.

        :returns:
            The default subdomain to be used in the URL map.
        """
        return self.app.config.get('tipfy', 'default_subdomain')

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

        return Map(rules, default_subdomain=self.get_default_subdomain())


class Tipfy(object):
    """The WSGI application."""
    #: True if the app is using App Engine dev server, False otherwise.
    dev = DEV
    #: The application ID as defined in *app.yaml*."""
    app_id = APP_ID
    #: The deployed version ID. Always '1' when using the dev server.
    version_id = VERSION_ID
    #: True if the app is running on App Engine, False otherwise.
    is_appengine = IS_APPENGINE
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

    def __init__(self, rules=None, config=None, debug=False):
        """Initializes the application.

        :param rules:
            URL rules definitions for the application.
        :param config:
            Dictionary with configuration for the application modules.
        :param debug:
            True if this is debug mode, False otherwise.
        """
        self.set_locals()
        self.debug = debug
        self.registry = {}
        self.error_handlers = {}

        if self.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        # Load default config and update with values for this instance.
        self.config = self.config_class(config, {'tipfy': default_config},
            ['tipfy'])

        # Load URL rules.
        self.router = self.router_class(self, rules)

    def __call__(self, environ, start_response):
        """Shortcut for :meth:`Tipfy.wsgi_app`."""
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        """This is the actual WSGI application.  This is not implemented in
        :meth:`__call__` so that middlewares can be applied without losing a
        reference to the class. So instead of doing this::

            app = MyMiddleware(app)

        It's a better idea to do this instead::

            app.wsgi_app = MyMiddleware(app.wsgi_app)

        Then you still have the original application object around and
        can continue to call methods on it.

        This idea comes from `Flask`_.

        :param environ:
            A WSGI environment.
        :param start_response:
            A callable accepting a status code, a list of headers and an
            optional exception context to start the response.
        """
        cleanup = True
        try:
            request = self.request_class(environ)
            self.set_locals(request)

            if request.method not in ALLOWED_METHODS:
                abort(501)

            match = self.router.match(request)
            response = self.router.dispatch(self, request, match)
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
                self.clear_locals()

        return response(environ, start_response)

    def handle_exception(self, request, exception):
        """Handles an exception. To set app-wide error handlers, define them
        using the corresponent HTTP status code in the ``error_handlers``
        dictionary of :class:`Tipfy`. For example, to set a custom
        `Not Found` page::

            class Handle404(RequestHandler):
                def handle_exception(self, exception, debug_mode):
                    return Response('Oops! I could swear this page was here!',
                        status=404)

            app = Tipfy([
                Rule('/', handler=MyHandler, name='home'),
            ])
            app.error_handlers[404] = Handle404

        When an ``HTTPException`` is raised using :func:`abort` or because the
        app could not fulfill the request, the error handler defined for the
        exception HTTP status code will be called. If it is not set, the
        exception is re-raised.

        .. note::
           Although being a :class:`RequestHandler`, the error handler will
           execute the ``handle_exception`` method after instantiation, instead
           of the method corresponding to the current request.

           Also, the error handler is responsible for setting the response
           status code, as shown in the example above.

        :param request:
            A :class:`Request` instance.
        :param exception:
            The raised exception.
        """
        if isinstance(exception, HTTPException):
            code = exception.code
        else:
            code = 500

        handler = self.error_handlers.get(code)
        if handler:
            rule = Rule('/', handler=handler, name='__exception__')
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

    def url_for(self, _name, **kwargs):
        """Returns a URL for a named :class:`Rule`.

        .. seealso:: :meth:`Router.build`.
        """
        return self.router.build(self.request, _name, kwargs)

    def get_test_client(self):
        """Creates a test client for this application.

        :returns:
            A ``werkzeug.Client`` with the WSGI application wrapped for tests.
        """
        from werkzeug import Client
        return Client(self, self.response_class, use_cookies=True)

    def run(self):
        """Runs the app using ``CGIHandler``. This must be called inside a
        ``main()`` function in the file defined in *app.yaml* to run the
        application::

            # ...

            app = Tipfy(rules=[
                Rule('/', name='home', handler=HelloWorldHandler),
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

    def set_locals(self, request=None):
        """Sets variables for a single request. Uses simple class attributes
        when running on App Engine and thread locals outside.

        :param request:
            A :class:`Request` instance, if any.
        """
        if self.is_appengine:
            Tipfy.app = self
            Tipfy.request = request
        else:
            local.app = self
            local.request = request

    def clear_locals(self):
        """Clears the variables set for a single request."""
        if self.is_appengine:
            Tipfy.app = Tipfy.request = None
        else:
            local.__release_local__()


def get_config(module, key=None, default=REQUIRED_VALUE):
    """Returns a configuration value for a module.

    .. seealso:: :meth:`Config.get_or_load`.
    """
    return Tipfy.app.get_config(module, key=key, default=default)


def get_valid_methods(handler):
    """Returns a list of HTTP methods supported by a handler.

    :param handler:
        A :class:`RequestHandler` instance.
    :returns:
        A list of HTTP methods supported by the handler.
    """
    return [method for method in ALLOWED_METHODS if
        getattr(handler, method.lower().replace('-', '_'), None)]


def url_for(_name, **kwargs):
    """Returns a URL for a named :class:`Rule`.

    .. seealso:: :meth:`Router.build`.
    """
    return Tipfy.app.url_for(_name, **kwargs)


def redirect(location, code=302):
    """Returns a response object with headers set for redirection to the
    given URI. This won't stop code execution, so you must return when
    calling this method::

        return redirect('/some-path')

    :param location:
        A relative or absolute URI (e.g., '../contacts').
    :param code:
        The HTTP status code for the redirect.
    :returns:
        A :class:`Response` object with headers set for redirection.
    """
    if not location.startswith('http'):
        # Make it absolute.
        location = urlparse.urljoin(Tipfy.app.request.url, location)

    return base_redirect(location, code)


def redirect_to(_name, _code=302, **kwargs):
    """Convenience method mixing ``werkzeug.redirect`` and :func:`url_for`:
    returns a response object with headers set for redirection to a URL
    built using a named :class:`Rule`.

    :param _name:
        The rule name.
    :param _code:
        The HTTP status code for the redirect.
    :param kwargs:
        Keyword arguments to build the URL.
    :returns:
        A :class:`Response` object with headers set for redirection.
    """
    return redirect(url_for(_name, **kwargs), code=_code)


def render_json_response(*args, **kwargs):
    """Renders a JSON response.

    :param args:
        Arguments to be passed to json_encode().
    :param kwargs:
        Keyword arguments to be passed to json_encode().
    :returns:
        A :class:`Response` object with a JSON string in the body and
        mimetype set to ``application/json``.
    """
    return Tipfy.response_class(json_encode(*args, **kwargs),
        mimetype='application/json')


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


# Add regex converter to the list of converters.
Map.default_converters = dict(Map.default_converters)
Map.default_converters['regex'] = RegexConverter

# Short aliases.
App = Tipfy
Handler = RequestHandler

# Locals.
if IS_APPENGINE:
    from werkzeug import LocalProxy
    local = None
    app = LocalProxy(lambda: Tipfy.app)
else:
    from werkzeug import Local
    local = Local()
    Tipfy.app = app = local('app')
    Tipfy.request = local('request')
