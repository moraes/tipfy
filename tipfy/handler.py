# -*- coding: utf-8 -*-
"""
    tipfy.handler
    ~~~~~~~~~~~~~

    Base request handler classes.

    :copyright: 2011 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import urlparse

import werkzeug.utils

from .app import abort, redirect
from .config import REQUIRED_VALUE


class BaseRequestHandler(object):
    """Base class to handle requests. This is the central piece for an
    application and provides access to the current WSGI app and request.
    Additionally it provides lazy access to auth, i18n and session stores,
    and several utilities to handle a request.

    Although it is convenient to extend this class or :class:`RequestHandler`,
    the only interface required by the WSGI app is the following:

        class RequestHandler(object):
            def __init__(self, request):
                pass

            def __call__(self):
                return Response()

    A Tipfy-compatible handler can be implemented using only these two methods.
    """
    def __init__(self, request, app=None):
        """Initializes the handler.

        :param request:
            A :class:`Request` instance.
        """
        if app:
            # App argument is kept for backwards compatibility. Previously we
            # called passing (app, request) but because view functions are now
            # supported only request is passed and app is an attribute of the
            # request object.
            from warnings import warn
            warn(DeprecationWarning("BaseRequestHandler.__init__(): the "
                "'app' argument is deprecated. The constructor must receive "
                "only the Request object."))
            self.app = request
            self.request = app
        else:
            self.request = request

        # A context for shared data, e.g., template variables.
        self.context = {}

    def __call__(self):
        """Executes a handler method. This is called by :class:`tipfy.app.App`
        and must return a :attr:`response_class` object. If :attr:`middleware`
        are defined, use their hooks to process the request or handle
        exceptions.

        :returns:
            A :attr:`response_class` instance.
        """
        return self.dispatch()

    def dispatch(self):
        try:
            request = self.request
            method_name = request.rule and request.rule.handler_method
            if not method_name:
                method_name = request.method.lower()

            method = getattr(self, method_name, None)
            if not method:
                # 405 Method Not Allowed.
                # The response MUST include an Allow header containing a
                # list of valid methods for the requested resource.
                # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.6
                self.abort(405, valid_methods=self.get_valid_methods())

            return self.make_response(method(**request.rule_args))
        except Exception, e:
            return self.handle_exception(exception=e)

    @werkzeug.utils.cached_property
    def app(self):
        """The current WSGI app instance.

        :returns:
            The current WSGI app instance.
        """
        return self.request.app

    @werkzeug.utils.cached_property
    def auth(self):
        """The auth store which provides access to the authenticated user and
        auth related functions.

        :returns:
            An auth store instance.
        """
        return self.request.auth

    @werkzeug.utils.cached_property
    def i18n(self):
        """The internationalization store which provides access to several
        translation and localization utilities.

        :returns:
            An i18n store instance.
        """
        return self.request.i18n

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
        return self.request.session_store

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

        .. warning: Deprecated. Use `self.app.config['module']['key']` instead.

        .. seealso:: :meth:`Config.get_config`.
        """
        from warnings import warn
        warn(DeprecationWarning("BaseRequestHandler.get_config(): this method "
            "is deprecated. Use self.app.config['module']['key'] instead."))
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
        response object that is an instance of
        :attr:`tipfy.app.App.response_class`.

        .. seealso:: :meth:`tipfy.app.App.make_response`.
        """
        return self.app.make_response(self.request, *rv)

    def redirect(self, location, code=302, response_class=None, body=None,
                 empty=False):
        """Returns a response object that redirects to the given location.

        This won't stop code execution, so you must return when calling it::

            return self.redirect('/some-path')

        :param location:
            A relative or absolute URI (e.g., '/contact'). If relative, it
            will be merged to the current request URL to form an absolute URL.
        :param code:
            The HTTP status code for the redirect. Default is 302.
        :param response_class:
            The class used to build the response. Default is
            :class:`tipfy.app.Response`.
        :param body:
            The response body. If not set uses a body with a standard message.
        :param empty:
            If True, returns a response with empty body.

            .. warning: Deprecated. Use `body=''` instead.
        :returns:
            A :class:`tipfy.app.Response` object with headers set for
            redirection.

        ..sealso:: :func:`tipfy.app.redirect`.
        """
        response_class = response_class or self.app.response_class

        if empty:
            from warnings import warn
            warn(DeprecationWarning("BaseRequestHandler.redirect(): the "
                "'empty' keyword argument is deprecated. Use body='' "
                "instead."))
            body = ''

        return redirect(location, code=code, response_class=response_class,
                        body=body)

    def redirect_to(self, _name, _code=302, _body=None, _empty=False,
                    **kwargs):
        """Returns a redirection response to a named URL rule.

        This is a convenience method that combines meth:`redirect` with
        meth:`url_for`.

        :param _name:
            The name of the :class:`tipfy.routing.Rule` to build a URL for.
        :param _code:
            The HTTP status code for the redirect. Default is 302.
        :param _body:
            The response body. If not set uses a body with a standard message.
        :param empty:
            If True, returns a response with empty body.

            .. warning: Deprecated. Use `body=''` instead.
        :param kwargs:
            Keyword arguments to build the URL.
        :returns:
            A :class:`tipfy.app.Response` object with headers set for
            redirection.
        """
        url = self.url_for(_name, _full=kwargs.pop('_full', True), **kwargs)
        return self.redirect(url, code=_code, body=_body, empty=_empty)

    def url_for(self, _name, **kwargs):
        """Returns a URL for a named :class:`Rule`.

        .. seealso:: :meth:`Router.url_for`.
        """
        return self.app.router.url_for(self.request, _name, kwargs)


class RequestHandler(BaseRequestHandler):
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

    def __call__(self):
        middleware = self.middleware or []

        # Execute before_dispatch middleware.
        for obj in middleware:
            func = getattr(obj, 'before_dispatch', None)
            if func:
                response = func(self)
                if response is not None:
                    break
        else:
            try:
                response = self.dispatch()
            except Exception, e:
                # Execute handle_exception middleware.
                for obj in reversed(middleware):
                    func = getattr(obj, 'handle_exception', None)
                    if func:
                        response = func(self, e)
                        if response is not None:
                            break
                else:
                    # If a middleware didn't return a response, reraise.
                    raise

        # Execute after_dispatch middleware.
        for obj in reversed(middleware):
            func = getattr(obj, 'after_dispatch', None)
            if func:
                response = func(self, response)

        # Done!
        return response


class RequestHandlerMiddleware(object):
    """Base class for :class:`RequestHandler` middleware."""
    def before_dispatch(self, handler):
        """Called before the handler method is executed.

        If the returned value is not None, stops the middleware chain and uses
        that value to create a response, and doesn't call the handler method.

        :param handler:
            A :class:`RequestHandler` instance.
        """

    def after_dispatch(self, handler, response):
        """Called after the handler method is executed.

        Must always return a response object.

        These are executed in reverse order.

        :param handler:
            A :class:`RequestHandler` instance.
        :param response:
            A :class:`tipfy.app.Response` instance.
        """
        return response

    def handle_exception(self, handler, exception):
        """Called if an exception occurs while executing the handler method.

        If the returned value is not None, stops the middleware chain and uses
        that value to create a response.

        These are executed in reverse order.

        :param handler:
            A :class:`RequestHandler` instance.
        :param exception:
            An exception.
        """
