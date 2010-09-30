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
from werkzeug import (Local, LocalProxy, Request as BaseRequest,
    Response as BaseResponse, cached_property, import_string,
    redirect as base_redirect)
from werkzeug.exceptions import HTTPException, InternalServerError, abort

from tipfy.config import Config, DEFAULT_VALUE, REQUIRED_VALUE
from tipfy.routing import HandlerPrefix, RegexConverter, Router, Rule
from tipfy.utils import json_decode, json_encode

__version__ = '0.7'
__version_info__ = tuple(int(n) for n in __version__.split('.'))

#: Default configuration values for this module. Keys are:
#:
#: auth_store_class
#:     The default auth store class to use in :class:`tipfy.Request`.
#:     Default is `tipfy.auth.appengine.AppEngineAuthStore`.
#:
#: session_store_class
#:     The default session store class to use in :class:`tipfy.Request`.
#:     Default is `tipfy.sessions.SessionStore`.
#:
#: server_name
#:     The server name used to calculate current subdomain. This only need
#:     to be defined to map URLs to subdomains. Default is None.
#:
#: default_subdomain
#:     The default subdomain used for rules without a subdomain defined.
#:     This only need to be defined to map URLs to subdomains. Default is ''.
default_config = {
    'auth_store_class':    'tipfy.auth.appengine.AppEngineAuthStore',
    'i18n_store_class':    'tipfy.i18n.I18nStore',
    'session_store_class': 'tipfy.sessions.SessionStore',
    'server_name':         None,
    'default_subdomain':   '',
}

# Allowed request methods.
ALLOWED_METHODS = frozenset(['DELETE', 'GET', 'HEAD', 'OPTIONS', 'POST', 'PUT',
    'TRACE'])

# App Engine flags.
SERVER_SOFTWARE = os.environ.get('SERVER_SOFTWARE', '')
APPLICATION_ID = os.environ.get('APPLICATION_ID', None)
CURRENT_VERSION_ID = os.environ.get('CURRENT_VERSION_ID', '1')
DEV = SERVER_SOFTWARE.startswith('Development')

try:
    import google.appengine
    APPENGINE = (APPLICATION_ID is not None and (DEV or
        SERVER_SOFTWARE.startswith('Google App Engine')))
except ImportError:
    APPENGINE = False


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
    #: before_dispatch(handler)
    #:     Called before the requested method is executed. If returns a
    #:     response, stops the middleware chain and uses that response, not
    #:     calling the requested method.
    #:
    #: after_dispatch(handler, response)
    #:     Called after the requested method is executed. Must always return
    #:     a response. All *after_dispatch* middleware are always executed.
    #:
    #: handle_exception(handler, exception)
    #:     Called if an exception occurs while executing the requested method.
    middleware = None

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
            self.abort(405, valid_methods=self.get_valid_methods())

        if not self.middleware:
            # No middleware are set: just execute the method.
            return self.app.make_response(method(*args, **kwargs))

        # Execute before_dispatch middleware.
        for obj in self.middleware:
            func = getattr(obj, 'before_dispatch', None)
            if func:
                response = func(self)
                if response is not None:
                    break
        else:
            try:
                response = self.app.make_response(method(*args, **kwargs))
            except Exception, e:
                # Execute handle_exception middleware.
                for obj in reversed(self.middleware):
                    func = getattr(obj, 'handle_exception', None)
                    if func:
                        response = func(self, e)
                        if response is not None:
                            break
                else:
                    # If a middleware didn't return a response, reraise.
                    raise

        # Execute after_dispatch middleware.
        for obj in reversed(self.middleware):
            func = getattr(obj, 'after_dispatch', None)
            if func:
                response = func(self, response)

        # Done!
        return response

    @cached_property
    def auth(self):
        """The auth store which provides access to the authenticated user and
        auth related functions.

        :returns:
            An auth store instance.
        """
        return self.request.auth_store

    @cached_property
    def session(self):
        """A session dictionary using the default session configuration.

        :returns:
            A dictionary-like object with the current session data.
        """
        return self.request.session_store.get_session()

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

        .. seealso:: :meth:`Config.get`.
        """
        return self.app.get_config(module, key=key, default=default)

    def handle_exception(self, exception=None):
        """Handles an exception. The default behavior is to reraise the
        exception (no exception handling is implemented).

        :param exception:
            The exception that was raised.
        """
        raise

    def redirect(self, location, code=302):
        """Returns a response object with headers set for redirection to the
        given URI.

        .. seealso:: :func:`redirect`.
        """
        return redirect(location, code)

    def redirect_to(self, _name, _code=302, **kwargs):
        """Convenience method mixing :meth:`redirect` and :methd:`url_for`:
        returns a response object with headers set for redirection to a URL
        built using a named :class:`Rule`.

        .. seealso:: :func:`redirect_to`.
        """
        return self.redirect(self.url_for(_name, **kwargs), code=_code)

    def url_for(self, _name, **kwargs):
        """Returns a URL for a named :class:`Rule`.

        .. seealso:: :meth:`Router.build`.
        """
        return self.app.router.build(self.request, _name, kwargs)

    def get_valid_methods(self):
        """Returns a list of methods supported by this handler. By default it
        will look for HTTP methods this handler implements. For different
        routing schemes, override this.

        :returns:
            A list of methods supported by this handler.
        """
        return [method for method in ALLOWED_METHODS if
            getattr(self, method.lower().replace('-', '_'), None)]


class Request(BaseRequest):
    """The :class:`Request` object contains all environment variables for the
    current request: GET, POST, FILES, cookies and headers.
    """
    #: URL adapter bound to a request.
    url_adapter = None
    #: Matched URL rule for a request.
    rule = None
    #: Keyword arguments from the matched URL rule.
    rule_args = None

    def __init__(self, environ):
        """Initializes the request. This also sets a context and registry to
        hold variables valid for a single request.
        """
        super(Request, self).__init__(environ)
        # A registry for objects in use during a request.
        self.registry = {}
        # A context for template variables.
        self.context = {}

    @cached_property
    def json(self):
        """If the mimetype is `application/json` this will contain the
        parsed JSON data.

        This function is borrowed from `Flask`_.

        :returns:
            The decoded JSON request data.
        """
        if self.mimetype == 'application/json':
            return json_decode(self.data)

    @cached_property
    def auth_store(self):
        """The auth store which provides access to the authenticated user and
        auth related functions.

        :returns:
            An auth store instance.
        """
        return Tipfy.app.auth_store_class(Tipfy.app, self)

    @cached_property
    def i18n_store(self):
        """
        """
        i18n = Tipfy.app.i18n_store
        i18n.set_locale_for_request(self)
        return i18n

    @cached_property
    def session_store(self):
        """The session store, responsible for managing sessions and flashes.

        :returns:
            A session store instance.
        """
        return Tipfy.app.session_store_class(Tipfy.app, self)

    @cached_property
    def session(self):
        """A session dictionary using the default session configuration.

        :returns:
            A dictionary-like object with the current session data.
        """
        return self.session_store.get_session()


class Response(BaseResponse):
    """A response object with default mimetype set to ``text/html``."""
    default_mimetype = 'text/html'


class Tipfy(object):
    """The WSGI application."""
    #: The application ID as defined in *app.yaml*."""
    application_id = APPLICATION_ID
    #: The deployed version ID. Always '1' when using the dev server.
    current_version_id = CURRENT_VERSION_ID
    #: True if the app is running on App Engine, False otherwise.
    appengine = APPENGINE
    #: True if the app is using App Engine dev server, False otherwise.
    dev = DEV
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
        self.config = self.config_class(config, {'tipfy': default_config})
        self.router = self.router_class(self, rules)

        if debug:
            logging.getLogger().setLevel(logging.DEBUG)

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
                response = self.make_response(e)
            except:
                if self.debug:
                    cleanup = False
                    raise

                # We only log unhandled non-HTTP exceptions. Users should
                # take care of logging in custom error handlers.
                logging.exception(e)
                response = self.make_response(InternalServerError())
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
                def handle_exception(self, exception):
                    logging.exception(exception)
                    return Response('Oops! I could swear this page was here!',
                        status=404)

            app = Tipfy([
                Rule('/', handler=MyHandler, name='home'),
            ])
            app.error_handlers[404] = Handle404

        When an ``HTTPException`` is raised using :func:`abort` or because the
        app could not fulfill the request, the error handler defined for the
        exception HTTP status code will be called. If it is not set, the
        exception is reraised.

        .. note::
           Although being a :class:`RequestHandler`, the error handler will
           execute the ``handle_exception`` method after instantiation, instead
           of the method corresponding to the current request.

           Also, the error handler is responsible for setting the response
           status code and logging the exception, as shown in the example
           above.

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
            kwargs = dict(exception=exception)
            return self.router.dispatch(self, request, (rule, kwargs),
                method='handle_exception')
        else:
            raise

    def make_response(self, *rv):
        """Converts the return value from a :class:`RequestHandler` to a real
        response object that is an instance of :attr:`response_class`.

        This function is borrowed from `Flask`_.

        :param rv:
            - If no arguments are passed, returns an empty response.
            - If a single argument is passed, the returned value varies
              according to its type:
              - :attr:`response_class`: the response is returned unchanged.
              - :class:`str`: a response is created with the string as body.
              - :class:`unicode`: a response is created with the string
                encoded to utf-8 as body.
              - a WSGI function: the function is called as WSGI application
                and buffered as response object.
              - None: a ValueError exception is raised.
            - If multiple arguments are passed, a response is created using
              the arguments.
        :returns:
            A :attr:`response_class` instance.
        """
        if not rv:
            return self.response_class()

        if len(rv) == 1:
            rv = rv[0]

            if isinstance(rv, self.response_class):
                return rv

            if isinstance(rv, basestring):
                return self.response_class(rv)

            if rv is None:
                raise ValueError('Handler did not return a response')

            return self.response_class.force_type(rv, self.request.environ)

        return self.response_class(*rv)

    def set_locals(self, request=None):
        """Sets variables for a single request. Uses simple class attributes
        when running on App Engine and thread locals outside.

        :param request:
            A :class:`Request` instance, if any.
        """
        if self.appengine:
            Tipfy.app = self
            Tipfy.request = request
        else:
            local.app = self
            local.request = request

    def clear_locals(self):
        """Clears the variables set for a single request."""
        if self.appengine:
            Tipfy.app = Tipfy.request = None
        else:
            local.__release_local__()

    def get_config(self, module, key=None, default=REQUIRED_VALUE):
        """Returns a configuration value for a module.

        .. seealso:: :meth:`Config.get`.
        """
        return self.config.get_config(module, key=key, default=default)

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
        if self.dev:
            # Fix issue #772.
            from tipfy.dev import fix_sys_path
            fix_sys_path()

        CGIHandler().run(self)

    @cached_property
    def auth_store_class(self):
        """Returns the configured auth store class.

        :returns:
            An auth store class.
        """
        return import_string(self.get_config('tipfy', 'auth_store_class'))

    @cached_property
    def session_store_class(self):
        """Returns the configured session store class.

        :returns:
            A session store class.
        """
        return import_string(self.get_config('tipfy', 'session_store_class'))

    @cached_property
    def i18n_store(self):
        """Returns the configured auth store class.

        :returns:
            An auth store class.
        """
        cls = import_string(self.get_config('tipfy', 'i18n_store_class'))
        return cls(self)


def get_config(module, key=None, default=REQUIRED_VALUE):
    """Returns a configuration value for a module.

    .. seealso:: :meth:`Config.get`.
    """
    return Tipfy.app.get_config(module, key=key, default=default)


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
        location = urlparse.urljoin(Tipfy.request.url, location)

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


# Short aliases.
App = Tipfy
Handler = RequestHandler

# Locals.
if APPENGINE:
    local = None
    app = LocalProxy(lambda: Tipfy.app)
    request = LocalProxy(lambda: Tipfy.request)
else:
    local = Local()
    Tipfy.app = app = local('app')
    Tipfy.request = request = local('request')
