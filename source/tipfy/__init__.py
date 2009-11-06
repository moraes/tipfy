# -*- coding: utf-8 -*-
"""
    tipfy
    ~~~~~

    Minimalist WSGI application and utilities.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from wsgiref.handlers import CGIHandler

# Werkzeug swiss knife.
from werkzeug import Local, LocalManager, Request, Response, import_string, \
    escape
from werkzeug.exceptions import HTTPException, BadRequest, Unauthorized, \
    Forbidden, NotFound, MethodNotAllowed, NotAcceptable, RequestTimeout, \
    Gone, LengthRequired, PreconditionFailed, RequestEntityTooLarge, \
    RequestURITooLarge, UnsupportedMediaType, InternalServerError, \
    NotImplemented, BadGateway, ServiceUnavailable
from werkzeug.routing import Map, Rule as WerkzeugRule, Submount, \
    EndpointPrefix, RuleTemplate, RequestRedirect

# Variable store for a single request.
local = Local()
local_manager = LocalManager([local])

# Proxies to the three special variables set on each request.
local.app = local.request = local.response = None
app, request, response = local('app'), local('request'), local('response')

# Allowed request methods.
ALLOWED_METHODS = frozenset(['get', 'post', 'head', 'options', 'put', 'delete',
    'trace'])


class RequestHandler(object):
    """Base request handler. Only implements the minimal interface required by
    `WSGIApplication`: the dispatch() method.
    """
    def dispatch(self, action, *args, **kwargs):
        """Executes a handler method. This method is called by the
        WSGIApplication and must always return a response object.

        :str action: the method to be executed.
        :dict kwargs: the arguments from the matched route.
        :return: a Response object.
        """
        method = getattr(self, action, None)
        if method:
            return method(*args, **kwargs)

        raise MethodNotAllowed()


class WSGIApplication(object):
    def __init__(self, config):
        """Initializes the application.

        :param config: Module with application settings.
        """
        self.config = config

        # Set an accessor to this instance.
        local.app = self

        # Set the url rules.
        self.url_map = get_url_map(self)

        # Cache for imported middlewares and default middlewares dict.
        self.middleware_classes = self.middleware_types = None
        self.middlewares = {}

        # Cache for imported handler classes.
        self.handlers = {}

    def __call__(self, environ, start_response):
        """Called by WSGI when a request comes in."""
        # Populate local with the request and response.
        local.request = Request(environ)
        local.response = Response()

        # Bind url map to the current request location.
        self.url_adapter = self.url_map.bind_to_environ(environ)

        # Get a response object.
        response = self.get_response()

        # Apply response middlewares.
        for method in self.middlewares.get('response', []):
            response = method(local.request, response)

        # Call the response object as a WSGI application.
        return response(environ, start_response)

    def get_response(self):
        try:
            # Check requested method.
            request_method = local.request.method.lower()
            if request_method not in ALLOWED_METHODS:
                raise MethodNotAllowed()

            # Apply request middlewares.
            for method in self.middlewares.get('request', []):
                response = method(local.request)
                if response:
                    return response

            # Match the path against registered rules.
            rule, kwargs = self.url_adapter.match(request.path,
                return_rule=True)

            # Import handler set in matched rule.
            if rule.handler not in self.handlers:
                self.handlers[rule.handler] = import_string(rule.handler)

            # Get the cached handler class.
            handler_class = self.handlers[rule.handler]

            # Apply handler middlewares.
            for method in self.middlewares.get('handler', []):
                response = method(local.request, handler_class, **kwargs)
                if response:
                    return response

            # Instantiate the handler.
            handler = handler_class()

            # Dispatch, passing method and rule parameters.
            response = handler.dispatch(request_method, **kwargs)

        except RequestRedirect, e:
            # Execute redirects set by the routing system.
            response = e
        except Exception, e:
            # Handle http and uncaught exceptions. This will apply exception
            # middlewares if they are set.
            response = handle_exception(self, e)

        return response


class Rule(WerkzeugRule):
    """Extends Werkzeug routing to support named routes. Names are the url
    identifiers that don't change, or should not change so often. If the map
    changes when using names, all url_for() calls remain the same.

    The endpoint in each rule becomes the 'name' and a new keyword argument
    'handler' defines the class it maps to. To get the handler, set
    return_rule=True when calling MapAdapter.match(), then access rule.handler.
    """
    def __init__(self, *args, **kwargs):
        self.handler = kwargs.pop('handler', kwargs.get('endpoint', None))
        WerkzeugRule.__init__(self, *args, **kwargs)

    def empty(self):
        """Returns an unbound copy of this rule. This can be useful if you
        want to reuse an already bound URL for another map."""
        defaults = None
        if self.defaults is not None:
            defaults = dict(self.defaults)
        return Rule(self.rule, defaults, self.subdomain, self.methods,
                    self.build_only, self.endpoint, self.strict_slashes,
                    self.redirect_to, handler=self.handler)


class PatchedCGIHandler(CGIHandler):
    """wsgiref.handlers.CGIHandler holds os.environ when imported. This class
    override this behaviour. Thanks to Kay framework for this patch.
    """
    def __init__(self):
        self.os_environ = {}
        CGIHandler.__init__(self)


def get_url_map(app):
    """Returns a `werkzeug.routing.Map` with the url rules defined for the app.
    Rules are cached in production only, and are updated when new versions are
    deployed.

    This implementation can be overriden defining a tipfy_get_url_map(app)
    function in appengine_config.py.
    """
    from google.appengine.api import memcache
    key = 'wsgi_app.urls.%s' % getattr(app.config, 'version_id', 1)
    urls = memcache.get(key)
    if not urls or app.config.dev:
        from urls import urls
        try:
            memcache.set(key, urls)
        except:
            import logging
            logging.info('Failed to save wsgi_app.urls to memcache.')

    return Map(urls)


def load_middlewares(app):
    """Imports middleware classes and extracts available middleware types, and
    sets them in the WSGI app.
    """
    app.middleware_classes = {}
    app.middleware_types = {}
    for class_spec in getattr(app.config, 'middleware_classes', []):
        app.middleware_classes[class_spec] = import_string(class_spec)
        for name in ('wsgi_app', 'request', 'response', 'handler', 'exception'):
            if hasattr(app.middleware_classes[class_spec], 'process_%s' % name):
                app.middleware_types.setdefault(name, []).append(class_spec)


def get_middlewares(app):
    """Instantiates middleware classes and returns a dictionary mapping
    middleware types to a list with the related middleware instance methods.
    """
    middlewares = {}
    instances = {}
    for name, specs in app.middleware_types.iteritems():
        for class_spec in specs:
            if class_spec not in instances:
                instances[class_spec] = app.middleware_classes[class_spec]()

            method = getattr(instances[class_spec], 'process_%s' % name)
            middlewares.setdefault(name, []).append(method)

    return middlewares


def make_bare_wsgi_app(config):
    """Returns a WSGI application instance without loading middlewares."""
    return WSGIApplication(config)


def make_wsgi_app(config):
    """Returns a instance of WSGIApplication with loaded middlewares."""
    app =  make_bare_wsgi_app(config)
    load_middlewares(app)
    return app


def run_wsgi_app(app):
    """Executes the application, optionally wrapping it by middlewares."""
    # Populate local with the WSGI app.
    local.app = app

    # Set middleware instances, if using middlewares.
    if app.middleware_classes is not None:
        app.middlewares = get_middlewares(app)

        # Apply wsgi_app middlewares.
        for method in app.middlewares.get('wsgi_app', []):
            app = method(app)

    # Wrap app by local_manager so that local is cleaned after each request.
    PatchedCGIHandler().run(local_manager.make_middleware(app))


def handle_exception(app, e):
    """Handles HTTPException or uncaught exceptions raised by the WSGI
    application, optionally applying exception middlewares.
    """
    for method in app.middlewares.get('exception', []):
        response = method(local.request, e)
        if response:
            return response

    if app.config.dev:
        raise

    if isinstance(e, HTTPException):
        return e

    return InternalServerError()


def redirect(location, code=302):
    """Return a response object (a WSGI application) that, if called,
    redirects the client to the target location.  Supported codes are 301,
    302, 303, 305, and 307.  300 is not supported because it's not a real
    redirect and 304 because it's the answer for a request with a request
    with defined If-Modified-Since headers.

    :param location: the location the response should redirect to.
    :param code: the redirect status code.
    """
    response = local.response
    assert code in (301, 302, 303, 305, 307), 'invalid code'
    response.data = \
        '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n' \
        '<title>Redirecting...</title>\n' \
        '<h1>Redirecting...</h1>\n' \
        '<p>You should be redirected automatically to target URL: ' \
        '<a href="%s">%s</a>.  If not click the link.' % \
        ((escape(location),) * 2)
    response.status_code = code
    response.headers['Location'] = location
    return response


def url_for(endpoint, full=False, method=None, **kwargs):
    """Returns an URL for a named Rule.

    :param endpoint: The rule endpoint
    :param full: If True, builds an absolute URL.
    :param method: The rule request method, in case there are different rules
        for different request methods.
    :param kwargs: Keyword arguments to build the Rule..
    """
    return local.app.url_adapter.build(endpoint, force_external=full,
        method=method, values=kwargs)


def redirect_to(endpoint, method=None, code=302, **kwargs):
    """Convenience function mixing redirect() and url_for()."""
    return redirect(url_for(endpoint, full=True, method=method, **kwargs),
        code=code)


def render_json_response(obj):
    """Renders a JSON response, automatically encoding `obj` to JSON."""
    from django.utils import simplejson
    local.response.data = simplejson.dumps(obj)
    local.response.mimetype = 'application/json'
    return local.response