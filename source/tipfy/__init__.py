# -*- coding: utf-8 -*-
"""
    tipfy
    ~~~~~

    Minimalist WSGI application and utilities.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from os import environ
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

#: Default configuration values for this module. Keys are:
#:   - ``dev``: ``True`` is this is the development server, ``False`` otherwise.
#:     By default checks the value of ``os.environ['SERVER_SOFTWARE']``.
#:   - ``app_id``: The application id. Default to the value set in
#:     ``os.environ['APPLICATION_ID']``.
#:   - ``version_id``: The current deplyment version id. Default to the value
#:     set in ``os.environ['CURRENT_VERSION_ID']``.
#:   - ``apps_installed``: A list of active app modules as a string.
#:   - ``apps_entry_points``: URL entry points for the installed apps.
#:   - ``middleware_classes``: A list of active middleware classes as a string.
default_config = {
    'dev': environ.get('SERVER_SOFTWARE', '').startswith('Dev'),
    'app_id': environ.get('APPLICATION_ID', None),
    'version_id': environ.get('CURRENT_VERSION_ID', '1'),
    'apps_installed': [],
    'apps_entry_points': {},
    'hooks': {},
}


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

        :param config:
            Dictionary with configuration for the application modules.
        """
        # Set an accessor to this instance.
        local.app = self

        # Load default config and update with config for this instance.
        self.config = Config(default_config)
        self.config.update(config)

        # Set the url rules.
        self.url_map = get_url_map(self)

        # Set the event manager and the configured hooks.
        self.event_manager = EventManager()
        self.event_manager.subscribe_multi(self.config.get('tipfy', 'hooks'))

        # Cache for loaded handler classes.
        self.handlers = {}

    def __call__(self, environ, start_response):
        """Called by WSGI when a request comes in."""
        # Populate local with the request and response.
        local.request = Request(environ)
        local.response = Response()

        # Bind url map to the current request location.
        self.url_adapter = self.url_map.bind_to_environ(environ)
        self.rule = self.rule_args = self.handler_class = None

        try:
            # Get a response object.
            response = self.get_response()

            # Apply response middlewares.
            self.event_manager.notify('before_response_sent', local.request,
                response)

        except RequestRedirect, e:
            # Execute redirects set by the routing system.
            response = e
        except Exception, e:
            # Handle http and uncaught exceptions. This will apply exception
            # middlewares if they are set.
            response = handle_exception(self, e)

        # Call the response object as a WSGI application.
        return response(environ, start_response)

    def get_response(self):
        # Check requested method.
        request_method = local.request.method.lower()
        if request_method not in ALLOWED_METHODS:
            raise MethodNotAllowed()

        # Match the path against registered rules.
        self.rule, self.rule_args = self.url_adapter.match(request.path,
            return_rule=True)

        # Import handler set in matched rule.
        if self.rule.handler not in self.handlers:
            self.handlers[self.rule.handler] = import_string(
                self.rule.handler)

        # Set an accessor to the current handler.
        self.handler_class = self.handlers[self.rule.handler]

        # Apply request middlewares.
        for response in self.event_manager.iter('before_handler_dispatch'):
            if response:
                return response

        # Instantiate handler and dispatch, passing method and rule arguments.
        return self.handler_class().dispatch(request_method, **self.rule_args)


class Config(dict):
    """A simple configuration dictionary keyed by module name."""
    def update(self, values):
        for module in values.keys():
            if not isinstance(values[module], dict):
                raise ValueError('Values in the configuration must be a dict.')

            if module not in self:
                self[module] = {}

            for key in values[module].keys():
                self[module][key] = values[module][key]

    def setdefault(self, module, values):
        if not isinstance(values, dict):
            raise ValueError('Values passed to Config.setdefault() must be a '
                'dict.')

        if module not in self:
            self[module] = {}

        for key in values.keys():
            self[module].setdefault(key, values[key])

    def get(self, module, key=None, default=None):
        if module not in self:
            return default

        if key is None:
            return self[module]
        elif key not in self[module]:
            return default

        return self[module][key]


class EventHandler(object):
    """A lazy callable used by :class:`EventManager`: events handlers are set
    as a string and only imported when used.
    """
    def __init__(self, handler_spec):
        """Builds the lazy callable.

        :param handler_spec:
            The handler callable that will handle the event. This is set as a
            string to be only imported when the callable is used.
        """
        self.handler_spec = handler_spec
        self.handler = None

    def __call__(self, *args, **kwargs):
        """Executes the event callable, importing it if it is not imported yet.

        :param args:
            Positional arguments to be passed to the callable.
        :param kwargs:
            Keyword arguments to be passed to the callable.
        :return:
            The value returned by the callable.
        """
        if self.handler is None:
            self.handler = import_string(self.handler_spec)

        return self.handler(*args, **kwargs)


class EventManager(object):
    def __init__(self, subscribers=None):
        """Initializes the event manager.

        :param subscribers:
            A dictionary with event names as keys and a list of handler specs
            as values.
        """
        self.subscribers = subscribers or {}

    def subscribe(self, name, handler_spec):
        """Subscribe a callable to a given event.

        :param name:
            The event name to subscribe to (a string).
        :param handler_spec:
            The handler callable that will handle the event. This is set as a
            string to be only imported when the callable is used.
        :return:
            ``None``.
        """
        self.subscribers.setdefault(name, []).append(EventHandler(handler_spec))

    def subscribe_multi(self, spec):
        """Subscribe multiple callables to multiple events.

        :param spec:
            A dictionary with event names as keys and a list of handler specs
            as values.
        :return:
            ``None``.
        """
        for name in spec.keys():
            self.subscribers.setdefault(name, []).extend(
                EventHandler(handler_spec) for handler_spec in spec[name])

    def iter(self, name, *args, **kwargs):
        """Notify all subscribers to a given event about its occurrence. This
        is a generator.

        :param name:
            The event name to notify subscribers about (a string).
        :param args:
            Positional arguments to be passed to the subscribers.
        :param kwargs:
            Keyword arguments to be passed to the subscribers.
        :yield:
            The result of the subscriber calls.
        """
        for subscriber in self.subscribers.get(name, []):
            yield subscriber(*args, **kwargs)

    def notify(self, name, *args, **kwargs):
        """Notify all subscribers to a given event about its occurrence. This
        uses :meth:`iter` and returns a list with all its results.

        :param name:
            The event name to notify subscribers about (a string).
        :param args:
            Positional arguments to be passed to the subscribers.
        :param kwargs:
            Keyword arguments to be passed to the subscribers.
        :return:
            A list with all results from the subscriber calls.
        """
        return [res for res in self.iter(name, *args, **kwargs)]


class Rule(WerkzeugRule):
    """Extends Werkzeug routing to support a handler definition for each Rule.
    Handler is a RequestHandler module and class specification, while endpoint
    is a friendly name used to build URL's. For example:

        Rule('/users', endpoint='user-list', handler='my_app:UsersHandler')

    Access to the URL '/users' loads `UsersHandler` class from `my_app` module,
    and to generate an URL to that page we use `url_for('user-list')`.
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
    """Returns a `werkzeug.routing.Map` with the URL rules defined for the app.
    Rules are cached in production and renewed on each deployment.
    """
    from google.appengine.api import memcache
    key = 'wsgi_app.rules.%s' % get_config(__name__, 'version_id')
    rules = memcache.get(key)
    if not rules or get_config(__name__, 'dev'):
        import urls
        try:
            rules = urls.get_rules()
        except AttributeError:
            raise
            # Deprecated and kept here for backwards compatibility. Set a
            # get_rules() function in urls.py returning all rules to avoid
            # already bound rules being binded when an exception occurs.
            rules = urls.urls

        try:
            memcache.set(key, rules)
        except:
            import logging
            logging.info('Failed to save wsgi_app.rules to memcache.')

    return Map(rules)


def make_wsgi_app(config):
    """Returns a instance of WSGIApplication with loaded middlewares."""
    return WSGIApplication(config)


def run_wsgi_app(app):
    """Executes the application, optionally wrapping it by middlewares."""
    # Populate local with the WSGI app.
    local.app = app

    # Wrap app by local_manager so that local is cleaned after each request.
    PatchedCGIHandler().run(local_manager.make_middleware(app))


def handle_exception(app, e):
    """Handles HTTPException or uncaught exceptions raised by the WSGI
    application, optionally applying exception middlewares.
    """
    for response in app.event_manager.notify('before_handle_exception',
        local.request, e):
        if response:
            return response

    if config['dev']:
        raise

    if isinstance(e, HTTPException):
        return e

    return InternalServerError()


def url_for(endpoint, full=False, method=None, **kwargs):
    """Builds and returns an URL for a named :class:`Rule`.

    :param endpoint:
        The rule endpoint.
    :param full:
        If True, builds an absolute URL. Otherwise, builds a relative one.
    :param method:
        The rule request method, in case there are different rules
        for different request methods.
    :param kwargs:
        Keyword arguments to build the URL.
    :return:
        An absolute or relative URL.
    """
    return local.app.url_adapter.build(endpoint, force_external=full,
        method=method, values=kwargs)


def redirect(location, code=302):
    """Return a response object (a WSGI application) that, if called,
    redirects the client to the target location.  Supported codes are 301,
    302, 303, 305, and 307.  300 is not supported because it's not a real
    redirect and 304 because it's the answer for a request with a request
    with defined If-Modified-Since headers.

    :param location:
        The location the response should redirect to.
    :param code:
        The redirect status code.
    :return:
        A ``werkzeug.Response`` object.
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


def redirect_to(endpoint, method=None, code=302, **kwargs):
    """Convenience function mixing :func:`redirect` and :func:`url_for`:
    redirects the client to a URL built using a named :class:`Rule`.
    """
    return redirect(url_for(endpoint, full=True, method=method, **kwargs),
        code=code)


def render_json_response(obj):
    """Renders a JSON response, automatically encoding `obj` to JSON."""
    from django.utils import simplejson
    local.response.data = simplejson.dumps(obj)
    local.response.mimetype = 'application/json'
    return local.response


def get_config(module, key, default=None):
    """Returns a configuration value for an module. If it is not already set,
    it'll load a ``default_config`` variable from the given module,
    update the app config with those default values and return the value for
    the given key. If the key is still not available, it'll return the
    given default value.

    Every `Tipfy`_ module that allows some kind of configuration sets a
    ``default_config`` global variable that is loaded by this function and
    used in case the requested configuration was not defined by the user.

    :param module:
        The configured module.
    :param key:
        The config key.
    :param default:
        The default value to be returned in case the key is not set.
    :return:
        A configuration value.
    """
    value = local.app.config.get(module, key, None)
    if value is None:
        default_config = import_string(module + ':default_config', silent=True)
        if default_config is None:
            value = default
        else:
            local.app.config.setdefault(module, default_config)
            value = local.app.config.get(module, key, default)

    return value