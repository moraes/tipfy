# -*- coding: utf-8 -*-
"""
    tipfy.app
    ~~~~~~~~~

    WSGI Application.

    :copyright: 2011 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import with_statement

import logging
import os
import urlparse
import wsgiref.handlers

# Werkzeug Swiss knife.
# Need to import werkzeug first otherwise py_zipimport fails.
import werkzeug
import werkzeug.exceptions
import werkzeug.urls
import werkzeug.utils
import werkzeug.wrappers

from . import default_config
from .config import Config, REQUIRED_VALUE
from .local import current_app, current_handler, get_request, local
from .routing import Router

#: Public interface.
HTTPException = werkzeug.exceptions.HTTPException
abort = werkzeug.exceptions.abort

#: TODO: remove from here.
from tipfy.appengine import (APPENGINE, APPLICATION_ID, CURRENT_VERSION_ID,
    DEV_APPSERVER)


class Request(werkzeug.wrappers.Request):
    """Provides all environment variables for the current request: GET, POST,
    FILES, cookies and headers.
    """
    #: The WSGI app.
    app = None
    #: Exception caught by the WSGI app during dispatch().
    exception = None
    #: URL adapter.
    rule_adapter = None
    #: Matched :class:`tipfy.routing.Rule`.
    rule = None
    #: Keyword arguments from the matched rule.
    rule_args = None
    #: A dictionary for request variables.
    registry = None

    def __init__(self, *args, **kwargs):
        super(Request, self).__init__(*args, **kwargs)
        self.registry = {}

    @werkzeug.utils.cached_property
    def auth(self):
        """The auth store which provides access to the authenticated user and
        auth related functions.

        :returns:
            An auth store instance.
        """
        return self.app.auth_store_class(self)

    @werkzeug.utils.cached_property
    def json(self):
        """If the mimetype is `application/json` this will contain the
        parsed JSON data.

        This function is borrowed from `Flask`_.

        :returns:
            The decoded JSON request data.
        """
        if self.mimetype == 'application/json':
            from tipfy.json import json_decode
            return json_decode(self.data)

    @werkzeug.utils.cached_property
    def i18n(self):
        """The internationalization store which provides access to several
        translation and localization utilities.

        :returns:
            An i18n store instance.
        """
        return self.app.i18n_store_class(self)

    @werkzeug.utils.cached_property
    def session(self):
        """A session dictionary using the default session configuration.

        :returns:
            A dictionary-like object with the current session data.
        """
        return self.session_store.get_session()

    @werkzeug.utils.cached_property
    def session_store(self):
        """The session store, responsible for managing sessions and flashes.

        :returns:
            A session store instance.
        """
        return self.app.session_store_class(self)

    def _get_rule_adapter(self):
        from warnings import warn
        warn(DeprecationWarning("Request.url_adapter: this attribute "
          "is deprecated. Use Request.rule_adapter instead."))
        return self.rule_adapter

    def _set_rule_adapter(self, adapter):
        from warnings import warn
        warn(DeprecationWarning("Request.url_adapter: this attribute "
          "is deprecated. Use Request.rule_adapter instead."))
        self.rule_adapter = adapter

    # Old name
    url_adapter = property(_get_rule_adapter, _set_rule_adapter)


class Response(werkzeug.wrappers.Response):
    """A response object with default mimetype set to ``text/html``."""
    default_mimetype = 'text/html'


class RequestContext(object):
    """Sets and releases the context locals used during a request.

    User meth:`App.get_test_context` to build a `RequestContext` for
    testing purposes.
    """
    def __init__(self, app, environ):
        """Initializes the request context.

        :param app:
            An :class:`App` instance.
        :param environ:
            A WSGI environment.
        """
        self.app = app
        self.environ = environ

    def __enter__(self):
        """Enters the request context.

        :returns:
            A :class:`Request` instance.
        """
        local.request = request = self.app.request_class(self.environ)
        local.app = request.app = self.app
        return request

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the request context.

        This will release the context locals except if an exception is caught
        in debug mode. In this case the locals are kept to be inspected.
        """
        if exc_type is None or not self.app.debug:
            local.__release_local__()


class App(object):
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
    #: Context class used when a request comes in.
    request_context_class = RequestContext

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
        """Called when a request comes in."""
        if self.debug and self.config['tipfy']['enable_debugger']:
            return self._debugged_wsgi_app(environ, start_response)

        return self.dispatch(environ, start_response)

    def dispatch(self, environ, start_response):
        """This is the actual WSGI application.  This is not implemented in
        :meth:`__call__` so that middlewares can be applied without losing a
        reference to the class. So instead of doing this::

            app = MyMiddleware(app)

        It's a better idea to do this instead::

            app.dispatch = MyMiddleware(app.dispatch)

        Then you still have the original application object around and
        can continue to call methods on it.

        This idea comes from `Flask`_.

        :param environ:
            A WSGI environment.
        :param start_response:
            A callable accepting a status code, a list of headers and an
            optional exception context to start the response.
        """
        with self.request_context_class(self, environ) as request:
            try:
                if request.method not in self.allowed_methods:
                    abort(501)

                rv = self.router.dispatch(request)
                response = self.make_response(request, rv)
            except Exception, e:
                try:
                    rv = self.handle_exception(request, e)
                    response = self.make_response(request, rv)
                except HTTPException, e:
                    response = self.make_response(request, e)
                except Exception, e:
                    if self.debug:
                        raise

                    logging.exception(e)
                    rv = werkzeug.exceptions.InternalServerError()
                    response = self.make_response(request, rv)

            return response(environ, start_response)

    def handle_exception(self, request, exception):
        """Handles an exception. To set app-wide error handlers, define them
        using the corresponent HTTP status code in the ``error_handlers``
        dictionary of :class:`App`. For example, to set a custom
        `Not Found` page::

            class Handle404(RequestHandler):
                def __call__(self):
                    logging.exception(self.request.exception)
                    return Response('Oops! I could swear this page was here!',
                        status=404)

            app = App([
                Rule('/', handler=MyHandler, name='home'),
            ])
            app.error_handlers[404] = Handle404

        When an ``HTTPException`` is raised using :func:`abort` or because the
        app could not fulfill the request, the error handler defined for the
        exception HTTP status code will be called. If it is not set, the
        exception is reraised.

        .. note::
           The exception is stored in the request object and accessible
           through `request.exception`.

           The error handler is responsible for setting the response
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
        if not handler:
            raise

        request.exception = exception
        rv = handler(request)
        if not isinstance(rv, werkzeug.wrappers.BaseResponse):
            if hasattr(rv, '__call__'):
                # If it is a callable but not a response, we call it again.
                rv = rv()

        return rv

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
        from warnings import warn
        warn(DeprecationWarning("App.get_config(): this method "
            "is deprecated. Use App.config['module']['key'] instead."))
        return self.config.get_config(module, key=key, default=default)

    def get_test_client(self):
        """Creates a test client for this application.

        :returns:
            A ``werkzeug.Client`` with the WSGI application wrapped for tests.
        """
        from werkzeug.test import Client
        return Client(self, self.response_class, use_cookies=True)

    def get_test_context(self, *args, **kwargs):
        """Creates a test client for this application.

        :param args:
            Positional arguments to construct a `werkzeug.test.EnvironBuilder`.
        :param kwargs:
            Keyword arguments to construct a `werkzeug.test.EnvironBuilder`.
        :returns:
            A :class:``RequestContext`` instance.
        """
        from werkzeug.test import EnvironBuilder
        builder = EnvironBuilder(*args, **kwargs)
        try:
            return self.request_context_class(self, builder.get_environ())
        finally:
            builder.close()

    def get_test_handler(self, *args, **kwargs):
        """Returns a handler set as a current handler for testing purposes.

        .. seealso:: :class:`tipfy.testing.CurrentHandlerContext`.

        :returns:
            A :class:`tipfy.testing.CurrentHandlerContext` instance.
        """
        from tipfy.testing import CurrentHandlerContext
        return CurrentHandlerContext(self, *args, **kwargs)

    def run(self):
        """Runs the app using ``CGIHandler``. This must be called inside a
        ``main()`` function in the file defined in *app.yaml* to run the
        application::

            # ...

            app = App(rules=[
                Rule('/', name='home', handler=HelloWorldHandler),
            ])

            def main():
                app.run()

            if __name__ == '__main__':
                main()

        """
        wsgiref.handlers.CGIHandler().run(self)

    @werkzeug.utils.cached_property
    def _debugged_wsgi_app(self):
        """Returns the WSGI app wrapped by an interactive debugger."""
        from tipfy.debugger import DebuggedApplication
        return DebuggedApplication(self.dispatch, evalex=True)

    @werkzeug.utils.cached_property
    def auth_store_class(self):
        """Returns the configured auth store class.

        :returns:
            An auth store class.
        """
        cls = self.config['tipfy']['auth_store_class']
        return werkzeug.utils.import_string(cls)

    @werkzeug.utils.cached_property
    def i18n_store_class(self):
        """Returns the configured i18n store class.

        :returns:
            An i18n store class.
        """
        cls = self.config['tipfy']['i18n_store_class']
        return werkzeug.utils.import_string(cls)

    @werkzeug.utils.cached_property
    def session_store_class(self):
        """Returns the configured session store class.

        :returns:
            A session store class.
        """
        cls = self.config['tipfy']['session_store_class']
        return werkzeug.utils.import_string(cls)

    # Old names
    wsgi_app = dispatch


def redirect(location, code=302, response_class=Response, body=None):
    """Returns a response object that redirects to the given location.

    Supported codes are 301, 302, 303, 305, and 307. 300 is not supported
    because it's not a real redirect and 304 because it's the answer for a
    request with a request with defined If-Modified-Since headers.

    :param location:
        A relative or absolute URI (e.g., '/contact'). If relative, it
        will be merged to the current request URL to form an absolute URL.
    :param code:
        The HTTP status code for the redirect. Default is 302.
    :param response_class:
        The class used to build the response. Default is :class:`Response`.
    :body:
        The response body. If not set uses a body with a standard message.
    :returns:
        A :class:`Response` object with headers set for redirection.
    """
    assert code in (301, 302, 303, 305, 307), 'invalid code'

    if location.startswith(('.', '/')):
        # Make it absolute.
        location = urlparse.urljoin(get_request().url, location)

    display_location = location
    if isinstance(location, unicode):
        location = werkzeug.urls.iri_to_uri(location)

    if body is None:
        body = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n' \
            '<title>Redirecting...</title>\n<h1>Redirecting...</h1>\n' \
            '<p>You should be redirected automatically to target URL: ' \
            '<a href="%s">%s</a>. If not click the link.' % \
            (location, display_location)

    response = response_class(body, code, mimetype='text/html')
    response.headers['Location'] = location
    return response


# Old names.
Tipfy = App
