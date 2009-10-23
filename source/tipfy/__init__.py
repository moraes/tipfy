# -*- coding: utf-8 -*-
"""
    tipfy
    ~~~~~

    WSGI application and utilities.

    This is much similar and intends to be as simple as App Engine's webapp.
    Some of the features:

      * Sessions using secure cookies.

      * Flash messages.

      * Interactive debugger.

      * Internationalization, as an optional extension.

      * No template engine enforced: use whatever you prefer.

      * Powerful and easier to use url routing system and url builder.

      * Handlers receive parameters as keyword arguments instead of positional
        arguments.

      * The requested handler method is dispatched by the handler, instead of
        the WSGI application, meaning that a handler can intercept an action
        before it is called.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from wsgiref.handlers import CGIHandler

from google.appengine.api import lib_config, memcache

# Werkzeug swiss knife.
from werkzeug import Local, LocalManager, Request, Response, import_string, \
    escape
from werkzeug.exceptions import HTTPException, MethodNotAllowed, \
    InternalServerError
from werkzeug.routing import Map, RequestRedirect, Rule as WerkzeugRule
from werkzeug.contrib.securecookie import SecureCookie

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

        :param config: An object, usually a module, with application settings.
        """
        self.config = config

        # Set an accessor to this instance.
        local.app = self

        # Set the url rules.
        self.url_map = config_handle.get_url_map(self)

        # Cache for imported handler classes.
        self.handlers = {}

    def __call__(self, environ, start_response):
        """Called by WSGI when a request comes in."""
        # Populate local with the wsgi app, request and response.
        local.app = self
        local.request = config_handle.get_request(self, environ)
        local.response = config_handle.get_response(self)
        handler = None

        try:
            # Check requested method.
            method = local.request.method.lower()
            if method not in ALLOWED_METHODS:
                raise MethodNotAllowed()

            # Bind url map to the current request location.
            self.url_adapter = config_handle.get_url_adapter(self, environ)

            # Match the path against registered rules.
            rule, kwargs = config_handle.get_url_match(self, local.request)

            # Import handler set in matched rule.
            if rule.handler not in self.handlers:
                self.handlers[rule.handler] = import_string(rule.handler)

            # Instantiate the handler.
            handler = self.handlers[rule.handler]()

            # Dispatch, passing method and rule parameters.
            response = handler.dispatch(method, **kwargs)

        except RequestRedirect, e:
            # Execute redirects set by the routing system.
            response = e
        except HTTPException, e:
            # Handle the exception.
            response = config_handle.handle_http_exception(handler, e)
        except Exception, e:
            # Handle everything else.
            response = config_handle.handle_exception(handler, e)

        # Call the response object as a WSGI application.
        return response(environ, start_response)


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
    key = 'wsgi_app.urls.%s' % app.config.version_id
    urls = memcache.get(key)
    if not urls or app.config.dev:
        from urls import urls
        try:
            memcache.set(key, urls)
        except:
            import logging
            logging.info('Failed to save wsgi_app.urls to memcache.')

    return Map(urls)


def get_url_adapter(app, environ):
    """Returns a `werkzeug.routing.MapAdapter` bound to the current request.

    This implementation can be overriden defining a tipfy_get_url_adapter(app,
    environ) function in appengine_config.py.
    """
    return app.url_map.bind_to_environ(environ)


def get_url_match(app, request):
    """Returns a tuple (rule, kwargs) with a `tipfy.Rule` and keyword arguments
    from the matched rule.

    This implementation can be overriden defining a tipfy_get_url_match(app,
    request) function in appengine_config.py.
    """
    return app.url_adapter.match(request.path, return_rule=True)


def handle_exception(handler, e):
    """Handles a HTTPException or Exception raised by the WSGI application.

    This is just a generic implementation. It can be overriden defining a
    tipfy_handle_http_exception(e) or tipfy_handle_exception(e) function in
    appengine_config.py.
    """
    if app.config.dev:
        raise

    if isinstance(e, HTTPException):
        return e

    return InternalServerError()


def make_wsgi_app(config):
    """Returns a instance of WSGIApplication, wrapped by local_manager so that
    local is cleaned after each request.
    """
    return local_manager.make_middleware(WSGIApplication(config))


def add_middleware(app):
    """Wraps WSGI middleware around a WSGI application object."""
    return config_handle.add_middleware(app)


def run_bare_wsgi_app(app):
    """Executes the WSGI application as a CGI script."""
    PatchedCGIHandler().run(app)


def run_wsgi_app(app):
    """Executes the WSGI application as a CGI script, wrapping it by custom
    middlewares.
    """
    run_bare_wsgi_app(add_middleware(app))


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


def get_session(key='tipfy.session'):
    """Returns a session value stored in a SecureCookie."""
    return SecureCookie.load_cookie(local.request, key=key,
        secret_key=local.app.config.session_secret_key)


def set_session(data, key='tipfy.session', force=True, **kwargs):
    """Sets a session value in a SecureCookie. See SecureCookie.save_cookie()
    for possible keyword arguments.
    """
    securecookie = SecureCookie(data=data,
        secret_key=local.app.config.session_secret_key)
    securecookie.save_cookie(local.response, key=key, force=force, **kwargs)


def get_flash(key='tipfy.flash'):
    """Reads and deletes a flash message. Flash messages are stored in a cookie
    and automatically deleted when read.
    """
    if key in local.request.cookies:
        from base64 import b64decode
        data = simplejson.loads(b64decode(local.request.cookies[key]))
        local.response.delete_cookie(key)
        return data


def set_flash(data, key='tipfy.flash'):
    """Sets a flash message. Flash messages are stored in a cookie
    and automatically deleted when read.
    """
    from base64 import b64encode
    local.response.set_cookie(key, value=b64encode(simplejson.dumps(data)))


def render_json_response(obj):
    """Renders a JSON response, automatically encoding `obj` to JSON."""
    from django.utils import simplejson
    local.response.data = simplejson.dumps(obj)
    local.response.mimetype = 'application/json'
    return local.response


# Application hooks. These are default settings that can be overridden
# adding tipfy_[config_key] definitions to appengine_config.py.
# It uses google.appengine.api.lib_config for the trick.
config_handle = lib_config.register('tipfy', {
    'add_middleware':  lambda app: app,
    'get_url_map':     get_url_map,
    'get_url_adapter': get_url_adapter,
    'get_url_match':   get_url_match,
    'get_request':     lambda app, environ: Request(environ),
    'get_response':    lambda app: Response(),
    'handle_http_exception': handle_exception,
    'handle_exception':      handle_exception,
})