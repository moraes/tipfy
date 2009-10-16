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
import sys
import logging
import traceback
from base64 import b64encode, b64decode
from wsgiref.handlers import CGIHandler
from django.utils import simplejson

from google.appengine.api import memcache

# Werkzeug swiss knife.
from werkzeug import Local, LocalManager, Request, Response, import_string, \
    cached_property, escape
from werkzeug.exceptions import HTTPException, BadRequest, Unauthorized, \
    Forbidden, NotFound, MethodNotAllowed, InternalServerError
from werkzeug.routing import Map, RequestRedirect, Rule as WerkzeugRule
from werkzeug.contrib.securecookie import SecureCookie

# Global variables for a single request.
local = Local()
local_manager = LocalManager([local])
# Proxies to the three special variables set on each request.
local.app = local.request = local.response = None
app = local('app')
request = local('request')
response = local('response')

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
        self.config = config

        # Set an accessor to this instance.
        local.app = self

        # Set the url rules.
        self.url_map = Map(get_urls())

        # Cache for imported handler classes.
        self.handlers = {}

    def __call__(self, environ, start_response):
        """Called by WSGI when a request comes in."""
        try:
            # Populate local with the wsgi app, request and response.
            local.app = self
            local.request = Request(environ)
            local.response = Response()

            # Check requested method.
            method = local.request.method.lower()
            if method not in ALLOWED_METHODS:
                raise MethodNotAllowed()

            # Bind url map to the current request location.
            self.url_adapter = self.url_map.bind_to_environ(environ)

            # Match the path against registered rules.
            rule, kwargs = self.url_adapter.match(local.request.path,
                return_rule=True)

            # Import handler set in matched rule.
            if rule.handler not in self.handlers:
                self.handlers[rule.handler] = import_string(rule.handler)

            # Instantiate the handler.
            handler = self.handlers[rule.handler]()

            # Dispatch, passing method and rule parameters.
            response = handler.dispatch(method, **kwargs)

        except RequestRedirect, e:
            # Execute automatic redirects set by the routing system.
            response = e
        except HTTPException, e:
            # Handle HTTP errors.
            response = handle_exception(e, e.code)
        except Exception, e:
            # Handle everything else as 500.
            response = handle_exception(e, 500)

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


def get_urls():
    """Returns the url rules for the app. Rules are cached in production only,
    and are updated when new versions are deployed.
    """
    key = 'wsgi_app.urls.%s' % local.app.config.version_id
    urls = memcache.get(key)
    if not urls or local.app.config.dev:
        from urls import urls
        try:
            memcache.set(key, urls)
        except:
            logging.info('Failed to save wsgi_app.urls to memcache.')

    return urls


def make_wsgi_app(config):
    """Instantiates and wraps the WSGI application so that cleaning up happens
    after each request.
    """
    return local_manager.make_middleware(WSGIApplication(config))


def run_wsgi_app(app):
    """Executes the WSGIApplication as a CGI script."""
    PatchedCGIHandler().run(app)


def log_exception():
    """Logs an exception traceback."""
    exc_type, exc_value, tb = sys.exc_info()
    buf = traceback.format_exception(exc_type, exc_value, tb, 30)
    log = ''.join(buf).strip().decode('utf-8', 'replace')
    logging.error(log)


def handle_exception(exception, code):
    """Renders a friendly page when something wrong occurs. When in
    development mode, just raise the exception.

    :Exception exception: the catched exception.
    :int code: HTTP status code.
    """
    if local.app.config.dev:
        # Just raise the exception when in development.
        raise
    else:
        # Log the exception traceback.
        log_exception()

        # Render a friendly page.
        # TODO
        response = local.response
        response.status_code = code
        return response


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


def url_for(name, full=False, method=None, **kwargs):
    """Builds a URL. If full is True, returns an absolute url."""
    return local.app.url_adapter.build(name, force_external=full,
        method=method, values=kwargs)


def redirect_to(name, method=None, **kwargs):
    """Convenience function mixing redirect() and url_for()."""
    return redirect(url_for(name, full=True, method=method, **kwargs))


def get_session(key='tipfy.session'):
    """Returns a session value stored in a SecureCookie."""
    return SecureCookie.load_cookie(local.request, key=key,
        secret_key=local.app.config.session_secret_key)


def set_session(data, key='tipfy.session', **kwargs):
    """Sets a session value in a SecureCookie. See SecureCookie.save_cookie()
    for possible keyword arguments.
    """
    securecookie = SecureCookie(data=data,
        secret_key=local.app.config.session_secret_key)
    securecookie.save_cookie(local.response, key=key, **kwargs)


def get_flash(key='tipfy.flash'):
    """Reads and deletes a flash message. Flash messages are stored in a cookie
    and automatically read and deleted on the next request.
    """
    if key in local.request.cookies:
        msg = simplejson.loads(b64decode(local.request.cookies[key]))
        local.response.delete_cookie(key)
        return msg


def set_flash(msg, key='tipfy.flash'):
    """Sets a flash message. Flash messages are stored in a cookie and
    automatically read and deleted on the next request.
    """
    local.response.set_cookie(key, value=b64encode(simplejson.dumps(msg)))


def render_json_response(obj):
    """Renders a JSON response, automatically encoding `obj` to JSON."""
    local.response.data = simplejson.dumps(obj)
    local.response.mimetype = 'application/json'
    return local.response