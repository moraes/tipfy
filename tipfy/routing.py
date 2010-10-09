# -*- coding: utf-8 -*-
"""
    tipfy.routing
    ~~~~~~~~~~~~~

    URL routing utilities.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from werkzeug import import_string, url_quote
from werkzeug.routing import (BaseConverter, EndpointPrefix, Map,
    Rule as BaseRule, RuleFactory, Subdomain, Submount)

from .app import local

__all__ = [
    'HandlerPrefix', 'NamePrefix', 'Rule', 'Subdomain', 'Submount',
]


class Router(object):
    def __init__(self, app, rules=None):
        """Initializes the router.

        :param app:
            A :class:`tipfy.Tipfy` instance.
        :param rules:
            A list of initial :class:`Rule` instances.
        """
        self.app = app
        self.handlers = {}
        self.map = self.create_map(rules)

    def add(self, rule):
        """Adds a rule to the URL map.

        :param rule:
            A :class:`Rule` or rule factory instance or a list of rules
            to be added.
        """
        if isinstance(rule, list):
            for r in rule:
                self.map.add(r)
        else:
            self.map.add(rule)

    def match(self, request):
        """Matches registered :class:`Rule` definitions against the current
        request and returns the matched rule and rule arguments.

        The URL adapter, matched rule and rule arguments will be set in the
        :class:`tipfy.Request` instance.

        Three exceptions can occur when matching the rules: ``NotFound``,
        ``MethodNotAllowed`` or ``RequestRedirect``. The WSGI app will handle
        raised exceptions.

        :param request:
            A :class:`tipfy.Request` instance.
        :returns:
            A tuple ``(rule, rule_args)`` with the matched rule and rule
            arguments.
        """
        # Bind the URL map to the current request
        request.url_adapter = self.map.bind_to_environ(request.environ,
            server_name=self.get_server_name(request))

        # Match the path against registered rules.
        match = request.rule, request.rule_args = request.url_adapter.match(
            return_rule=True)
        return match

    def dispatch(self, request, match, method=None):
        """Dispatches a request. This instantiates and calls a
        :class:`tipfy.RequestHandler` based on the matched :class:`Rule`.

        :param request:
            A :class:`tipfy.Request` instance.
        :param match:
            A tuple ``(rule, rule_args)`` with the matched rule and rule
            arguments.
        :param method:
            A method to be used instead of using the request or handler method.
        :returns:
            A :class:`tipfy.Response` instance.
        """
        cls, method, kwargs = self.get_dispatch_spec(request, match, method)

        # Instantiate the handler.
        local.current_handler = handler = cls(self.app, request)
        try:
            # Dispatch the requested method.
            return handler(method, **kwargs)
        except Exception, e:
            if method == 'handle_exception':
                # We are already handling an exception.
                raise

            # If the handler implements exception handling, let it handle it.
            return self.app.make_response(request, handler.handle_exception(e))

    def get_dispatch_spec(self, request, match, method=None):
        """Returns the handler, method and keyword arguments to be executed
        for the matched rule.

        When the ``rule.handler`` attribute is set as a string, it is replaced
        by the imported class. If the handler string is defined using the
        ``Handler:method`` notation, the method will be stored in the rule.

        When the handler is dynamically imported an ``ImportError`` or
        ``AttributeError`` can be raised if it is badly defined. The WSGI app
        will handle raised exceptions.

        :param request:
            A :class:`tipfy.Request` instance.
        :param match:
            A tuple ``(rule, rule_args)`` with the matched rule and rule
            arguments.
        :param method:
            A method to be used instead of using the request or handler method.
        :returns:
            A tuple ``(handler_class, method, kwargs)`` to be executed.
        """
        rule, rule_args = match

        if isinstance(rule.handler, basestring):
            parts = rule.handler.rsplit(':', 1)
            handler = parts[0]
            if len(parts) > 1:
                rule.handler_method = parts[1]

            if handler not in self.handlers:
                self.handlers[handler] = import_string(handler)

            rule.handler = self.handlers[handler]

        if not method:
            if rule.handler_method is None:
                method = request.method.lower().replace('-', '_')
            else:
                method = rule.handler_method

        return rule.handler, method, rule_args

    def build(self, request, name, kwargs):
        """Returns a URL for a named :class:`Rule`. This is the central place
        to build URLs for an app. It is used by :meth:`RequestHandler.url_for`,
        which conveniently pass the request object so you don't have to.

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

    def create_map(self, rules=None):
        """Returns a ``werkzeug.routing.Map`` instance with the given
        :class:`Rule` definitions.

        :param rules:
            A list of :class:`Rule` definitions.
        :returns:
            A ``werkzeug.routing.Map`` instance.
        """
        return Map(rules, default_subdomain=self.get_default_subdomain())

    def get_default_subdomain(self):
        """Returns the default subdomain for rules without a subdomain
        defined. By default it returns the configured default subdomain.

        :returns:
            The default subdomain to be used in the URL map.
        """
        return self.app.config['tipfy']['default_subdomain']

    def get_server_name(self, request):
        """Returns the server name used to bind the URL map. By default it
        returns the configured server name. Extend this if you want to
        calculate the server name dynamically (e.g., to match subdomains
        from multiple domains).

        :param request:
            A :class:`tipfy.Request` instance.
        :returns:
            The server name used to build the URL adapter.
        """
        return self.app.config['tipfy']['server_name']


class Rule(BaseRule):
    """Extends Werkzeug routing to support handler and name definitions for
    each Rule. Handler is a :class:`tipfy.RequestHandler` class and name is a
    friendly name used to build URL's. For example::

        Rule('/users', name='user-list', handler='my_app:UsersHandler')

    Access to the URL ``/users`` loads ``UsersHandler`` class from
    ``my_app`` module. To generate a URL to that page, use
    :meth:`RequestHandler.url_for` inside a handler::

        url = self.url_for('user-list')
    """
    def __init__(self, path, handler=None, name=None, **kwargs):
        self.name = kwargs.pop('endpoint', name)
        self.handler = handler or self.name
        self.handler_method = None
        super(Rule, self).__init__(path, endpoint=self.name, **kwargs)

    def empty(self):
        """Returns an unbound copy of this rule. This can be useful if you
        want to reuse an already bound URL for another map.
        """
        defaults = None
        if self.defaults is not None:
            defaults = dict(self.defaults)

        return Rule(self.rule, handler=self.handler, name=self.name,
            defaults=defaults, subdomain=self.subdomain, methods=self.methods,
            build_only=self.build_only, strict_slashes=self.strict_slashes,
            redirect_to=self.redirect_to)


class HandlerPrefix(RuleFactory):
    """Prefixes all handler values (which must be strings for this factory) of
    nested rules with another string. For example, take these rules::

        rules = [
            Rule('/', name='index', handler='my_app.handlers.IndexHandler'),
            Rule('/entry/<entry_slug>', name='show',
                handler='my_app.handlers.ShowHandler'),
        ]

    You can wrap them by ``HandlerPrefix`` to define the handler module and
    avoid repetition. This is equivalent to the above::

        rules = [
            HandlerPrefix('my_app.handlers.', [
                Rule('/', name='index', handler='IndexHandler'),
                Rule('/entry/<entry_slug>', name='show',
                    handler='ShowHandler'),
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
    """A :class:`Rule` converter that matches a regular expression::

        Rule(r'/<regex(".*$"):name>')

    This is mainly useful to match subdomains. Don't use it for normal rules.
    """
    def __init__(self, map, *items):
        BaseConverter.__init__(self, map)
        self.regex = items[0]


# Add regex converter to the list of converters.
Map.default_converters = dict(Map.default_converters)
Map.default_converters['regex'] = RegexConverter
# Alias only because we prefer "name" instead of "endpoint" in rules.
NamePrefix = EndpointPrefix
