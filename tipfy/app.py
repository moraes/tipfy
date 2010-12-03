# -*- coding: utf-8 -*-
"""
    tipfy.app
    ~~~~~~~~~

    WSGI Application and RequestHandler.

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
from werkzeug import (Local, Request as BaseRequest, Response as BaseResponse,
    cached_property, import_string, redirect as base_redirect)
from werkzeug.exceptions import HTTPException, InternalServerError, abort

#: Context-local.
local = Local()
#: A proxy to the active handler for a request. This is intended to be used by
#: functions called out of a handler context. Usage is generally discouraged:
#: it is preferable to pass the handler as argument when possible and only use
#: this as last alternative -- when a proxy is really needed.
#:
#: For example, the :func:`tipfy.utils.url_for` function requires the current
#: request to generate a URL. As its purpose is to be assigned to a template
#: context or other objects shared between requests, we use `current_handler`
#: there to dynamically get the currently active handler.
current_handler = local('current_handler')
#: Same as current_handler, only for the active WSGI app.
current_app = local('current_app')

from . import default_config
from .config import Config, REQUIRED_VALUE
from .routing import Router, Rule
from .utils import json_decode

__all__ = [
    'HTTPException', 'Request', 'RequestHandler', 'Response', 'Tipfy',
    'current_handler', 'APPENGINE', 'APPLICATION_ID', 'CURRENT_VERSION_ID',
    'DEV_APPSERVER',
]

# App Engine flags.
SERVER_SOFTWARE = os.environ.get('SERVER_SOFTWARE', '')
#: The application ID as defined in *app.yaml*.
APPLICATION_ID = os.environ.get('APPLICATION_ID')
#: The deployed version ID. Always '1' when using the dev server.
CURRENT_VERSION_ID = os.environ.get('CURRENT_VERSION_ID', '1')
#: True if the app is using App Engine dev server, False otherwise.
DEV_APPSERVER = SERVER_SOFTWARE.startswith('Development')
#: True if the app is running on App Engine, False otherwise.
APPENGINE = (APPLICATION_ID is not None and (DEV_APPSERVER or
    SERVER_SOFTWARE.startswith('Google App Engine')))


class RequestHandler(object):
    """Base class to handle requests. This is the central piece for an
    application and provides access to the current WSGI app and request.
    Additionally it provides lazy access to auth, i18n and session stores,
    and several utilities to handle a request.
    """
    #: A list of middleware instances. A middleware can implement three
    #: methods that are called before and after the current request method
    #: is executed, or if an exception occurs:
    #:
    #: before_dispatch(handler)
    #:     Called before the requested method is executed. If returns a
    #:     response, stops the middleware chain and uses that response, not
    #:     calling the requested method.
    #:
    #: after_dispatch(handler, response)
    #:     Called after the requested method is executed. Must always return
    #:     a response. These are executed in reverse order.
    #:
    #: handle_exception(handler, exception)
    #:     Called if an exception occurs while executing the requested method.
    #:     These are executed in reverse order.
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
        # A context for shared data, e.g., template variables.
        self.context = {}

    def __call__(self, _method, *args, **kwargs):
        """Executes a handler method. This is called by :class:`Tipfy` and
        must return a :attr:`response_class` object. If :attr:`middleware` are
        defined, use their hooks to process the request or handle exceptions.

        :param _method:
            The method to be dispatched, normally the request method in
            lower case, e.g., 'get', 'post', 'head' or 'put'.
        :param kwargs:
            Keyword arguments from the matched :class:`Rule`.
        :returns:
            A :attr:`response_class` instance.
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
            return self.make_response(method(*args, **kwargs))

        # Execute before_dispatch middleware.
        for obj in self.middleware:
            func = getattr(obj, 'before_dispatch', None)
            if func:
                response = func(self)
                if response is not None:
                    break
        else:
            try:
                response = self.make_response(method(*args, **kwargs))
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
        return self.app.auth_store_class(self)

    @cached_property
    def i18n(self):
        """The internationalization store which provides access to several
        translation and localization utilities.

        :returns:
            An i18n store instance.
        """
        return self.app.i18n_store_class(self)

    @cached_property
    def session(self):
        """A session dictionary using the default session configuration.

        :returns:
            A dictionary-like object with the current session data.
        """
        return self.session_store.get_session()

    @cached_property
    def session_store(self):
        """The session store, responsible for managing sessions and flashes.

        :returns:
            A session store instance.
        """
        return self.app.session_store_class(self)

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

        .. seealso:: :meth:`Config.get_config`.
        """
        return self.app.config.get_config(module, key=key, default=default)

    def get_valid_methods(self):
        """Returns a list of methods supported by this handler. By default it
        will look for HTTP methods this handler implements. For different
        routing schemes, override this.

        :returns:
            A list of methods supported by this handler.
        """
        return [method for method in self.app.allowed_methods if
            getattr(self, method.lower().replace('-', '_'), None)]

    def handle_exception(self, exception=None):
        """Handles an exception. The default behavior is to reraise the
        exception (no exception handling is implemented).

        :param exception:
            The exception that was raised.
        """
        raise

    def make_response(self, *rv):
        """Converts the returned value from a :class:`RequestHandler` to a
        response object that is an instance of :attr:`Tipfy.response_class`.

        .. seealso:: :meth:`Tipfy.make_response`.
        """
        return self.app.make_response(self.request, *rv)

    def redirect(self, location, code=302, empty=False):
        """Returns a response object with headers set for redirection to the
        given URI. This won't stop code execution, so you must return when
        calling this method::

            return self.redirect('/some-path')

        :param location:
            A relative or absolute URI (e.g., '../contacts'). If relative, it
            will be joined to the current request URL.
        :param code:
            The HTTP status code for the redirect.
        :param empty:
            If True, returns a response without body. By default Werkzeug sets
            a standard message in the body.
        :returns:
            A :class:`Response` object with headers set for redirection.
        """
        if not location.startswith('http'):
            # Make it absolute.
            location = urlparse.urljoin(self.request.url, location)

        response = base_redirect(location, code)

        if empty:
            response.data = ''

        return response

    def redirect_to(self, _name, _code=302, _empty=False, **kwargs):
        """Convenience method mixing ``werkzeug.redirect`` and :func:`url_for`:
        returns a response object with headers set for redirection to a URL
        built using a named :class:`Rule`.

        :param _name:
            The rule name.
        :param _code:
            The HTTP status code for the redirect.
        :param _empty:
            If True, returns a response without body. By default Werkzeug sets
            a standard message in the body.
        :param kwargs:
            Keyword arguments to build the URL.
        :returns:
            A :class:`Response` object with headers set for redirection.
        """
        return self.redirect(self.url_for(_name, _full=kwargs.pop('_full',
            True), **kwargs), code=_code, empty=_empty)

    def url_for(self, _name, **kwargs):
        """Returns a URL for a named :class:`Rule`.

        .. seealso:: :meth:`Router.build`.
        """
        return self.app.router.build(self.request, _name, kwargs)


class Request(BaseRequest):
    """Provides all environment variables for the current request: GET, POST,
    FILES, cookies and headers.
    """
    #: URL adapter.
    url_adapter = None
    #: Matched :class:`tipfy.Rule`.
    rule = None
    #: Keyword arguments from the matched rule.
    rule_args = None

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


class Response(BaseResponse):
    """A response object with default mimetype set to ``text/html``."""
    default_mimetype = 'text/html'


class Tipfy(object):
    """The WSGI application."""
    # Allowed request methods.
    allowed_methods = frozenset(['DELETE', 'GET', 'HEAD', 'OPTIONS', 'POST',
        'PUT', 'TRACE'])
    #: Default class for requests.
    request_class = Request
    #: Default class for responses.
    response_class = Response
    #: Default class for the configuration object.
    config_class = Config
    #: Default class for the configuration object.
    router_class = Router

    def __init__(self, rules=None, config=None, debug=False):
        """Initializes the application.

        :param rules:
            URL rules definitions for the application.
        :param config:
            Dictionary with configuration for the application modules.
        :param debug:
            True if this is debug mode, False otherwise.
        """
        local.current_app = self
        self.debug = debug
        self.registry = {}
        self.error_handlers = {}
        self.config = self.config_class(config, {'tipfy': default_config})
        self.router = self.router_class(self, rules)

        if debug:
            logging.getLogger().setLevel(logging.DEBUG)

    def __call__(self, environ, start_response):
        """Shortcut for :meth:`Tipfy.wsgi_app`."""
        local.current_app = self
        if self.debug and self.config['tipfy']['enable_debugger']:
            return self._debugged_wsgi_app(environ, start_response)

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
            if request.method not in self.allowed_methods:
                abort(501)

            match = self.router.match(request)
            response = self.router.dispatch(request, match)
        except Exception, e:
            try:
                response = self.handle_exception(request, e)
            except HTTPException, e:
                response = self.make_response(request, e)
            except Exception, e:
                if self.debug:
                    cleanup = not self.config['tipfy']['enable_debugger']
                    raise

                # We only log unhandled non-HTTP exceptions. Users should
                # take care of logging in custom error handlers.
                logging.exception(e)
                response = self.make_response(request, InternalServerError())
        finally:
            if cleanup:
                local.__release_local__()

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
            A :attr:`request_class` instance.
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
            return self.router.dispatch(request, (rule, kwargs),
                method='handle_exception')
        else:
            raise

    def make_response(self, request, *rv):
        """Converts the returned value from a :class:`RequestHandler` to a
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
                raise ValueError('RequestHandler did not return a response.')

            return self.response_class.force_type(rv, request.environ)

        return self.response_class(*rv)

    def get_config(self, module, key=None, default=REQUIRED_VALUE):
        """Returns a configuration value for a module.

        .. seealso:: :meth:`Config.get_config`.
        """
        return self.config.get_config(module, key=key, default=default)

    def get_test_client(self):
        """Creates a test client for this application.

        :returns:
            A ``werkzeug.Client`` with the WSGI application wrapped for tests.
        """
        from werkzeug import Client
        return Client(self, self.response_class, use_cookies=True)

    def get_test_handler(self, *args, **kwargs):
        """Returns a handler set as a current handler for testing purposes.

        .. seealso:: :class:`tipfy.testing.CurrentHandlerContext`.

        :returns:
            A :class:`tipfy.testing.CurrentHandlerContext` instance.
        """
        from .testing import CurrentHandlerContext
        return CurrentHandlerContext(self, *args, **kwargs)

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
        CGIHandler().run(self)

    @cached_property
    def _debugged_wsgi_app(self):
        """Returns the WSGI app wrapped by an interactive debugger."""
        from .debugger import DebuggedApplication
        return DebuggedApplication(self.wsgi_app, evalex=True)

    @cached_property
    def auth_store_class(self):
        """Returns the configured auth store class.

        :returns:
            An auth store class.
        """
        return import_string(self.config['tipfy']['auth_store_class'])

    @cached_property
    def i18n_store_class(self):
        """Returns the configured i18n store class.

        :returns:
            An i18n store class.
        """
        return import_string(self.config['tipfy']['i18n_store_class'])

    @cached_property
    def session_store_class(self):
        """Returns the configured session store class.

        :returns:
            A session store class.
        """
        return import_string(self.config['tipfy']['session_store_class'])
