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

from tipfy import (default_config, local, local_manager, HTTPException,
    import_string, InternalServerError, Map, MethodNotAllowed, Request,
    RequestRedirect, Response)
from tipfy import config
from tipfy import hooks

# Allowed request methods.
ALLOWED_METHODS = frozenset(['get', 'post', 'head', 'options', 'put', 'delete',
    'trace'])


class RequestHandler(object):
    """Base request handler. Implements the minimal interface required by
    :class:`WSGIApplication`: the ``dispatch()`` method.
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

        # Initialize every middleware.
        middleware = [m() for m in self.middleware]

        # Execute pre_dispatch() middleware.
        for m in middleware:
            if getattr(m, 'pre_dispatch', None):
                response = m.pre_dispatch(self)
                if response is not None:
                    break
        else:
            try:
                # Execute the requested method.
                response = method(*args, **kwargs)
            except Exception, e:
                # Execute handle_exception() middleware.
                for m in reversed(middleware):
                    if getattr(m, 'handle_exception', None):
                        response = m.handle_exception(self, e)
                        if response:
                            return response
                else:
                    raise

        # Execute post_dispatch() middleware.
        for m in reversed(middleware):
            if getattr(m, 'post_dispatch', None):
                response = m.post_dispatch(self, response)

        # Done!
        return response


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

        # Setup extensions.
        for module in self.config.get('tipfy', 'extensions', []):
            import_string(module + ':setup')(self)

    def __call__(self, environ, start_response):
        """Called by WSGI when a request comes in."""
        # Apply pre-init-request hooks.
        for request in self.hooks.iter('pre_init_request', environ):
            if request is not None:
                break
        else:
            request = self.request_class(environ)

        # Set local variables for a single request.
        local.app = self
        local.request = request
        local.response = self.response_class()

        # Bind url map to the current request location.
        self.url_adapter = self.url_map.bind_to_environ(environ,
            server_name=self.config.get('tipfy', 'server_name', None),
            subdomain=self.config.get('tipfy', 'subdomain', None))

        self.rule = self.rule_args = None

        try:
            # Apply pre-match-url hooks.
            for res in self.hooks.iter('pre_match_url'):
                if res is not None:
                    self.rule, self.rule_args = res
                    break
            else:
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
                if self.rule.handler not in self.handlers:
                    self.handlers[self.rule.handler] = import_string(
                        self.rule.handler)

                # Instantiate handler and dispatch request method.
                response = self.handlers[self.rule.handler]().dispatch(method,
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

        # Apply pre-end-request hooks.
        for r in self.hooks.iter('pre_end_request', response):
            if r is not None:
                response = r
                break

        # Call the response object as a WSGI application.
        return response(environ, start_response)

    def get_url_map(self):
        """Returns ``werkzeug.routing.Map`` with the URL rules defined for the
        application. Rules are cached in production; the cache is automatically
        renewed on each deployment.

        :return:
            A ``werkzeug.routing.Map`` instance.
        """
        from google.appengine.api import memcache
        config = self.config.get('tipfy')
        key = 'wsgi_app.rules.%s.%s' % (config.get('wsgi_app_id'),
            config.get('version_id'))
        rules = memcache.get(key)
        if not rules or config.get('dev'):
            rules = import_string('urls:get_rules')()
            try:
                memcache.set(key, rules)
            except:
                logging.info('Failed to save wsgi_app.rules to memcache.')

        return Map(rules, **config.get('url_map_kwargs'))

    def handle_exception(self, e):
        """Handles HTTPException or uncaught exceptions raised by the WSGI
        application, optionally applying exception hooks.

        :param e:
            The catched exception.
        :return:
            A ``werkzeug.Response`` object, if the exception is not raised.
        """
        for response in self.hooks.iter('pre_handle_exception', e):
            if response:
                return response

        if self.config.get('tipfy', 'dev'):
            raise

        logging.exception(e)

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
    return WSGIApplication(config)


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

    # Apply pre-run hooks.
    for res in app.hooks.iter('pre_run_app', app):
        if res is not None:
            app = res

    # Wrap app by local_manager so that local is cleaned after each request.
    PatchedCGIHandler().run(local_manager.make_middleware(app))


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
    else:
        if sys.path != _ULTIMATE_SYS_PATH:
            sys.path[:] = _ULTIMATE_SYS_PATH


__all__ = ['make_wsgi_app', 'RequestHandler', 'run_wsgi_app', 'WSGIApplication']
