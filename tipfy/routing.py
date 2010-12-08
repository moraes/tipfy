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
            request_method = request.method.lower().replace('-', '_')

            if rule.handler_method is None:
                method = request_method
            else:
                method = rule.handler_method
                # Idea: if rule has methods defined, append the current
                # request method to the method name (or add a 'method_sufix'
                # argument to rule to enable it?).
                # if rule.methods:
                #     method += '_' + request_method

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
    """A Rule represents one URL pattern. Tipfy extends Werkzeug's Rule
    to support handler and name definitions. Handler is the
    :class:`tipfy.RequestHandler` class that will handle the request and name
    is a unique name used to build URL's. For example::

        Rule('/users', name='user-list', handler='my_app:UsersHandler')

    Access to the URL ``/users`` loads ``UsersHandler`` class from
    ``my_app`` module. To generate a URL to that page, use
    :meth:`RequestHandler.url_for` inside a handler::

        url = self.url_for('user-list')
    """
    def __init__(self, path, name=None, handler=None, **kwargs):
        """There are some options for `Rule` that change the way it behaves
        and are passed to the `Rule` constructor. Note that besides the
        rule-string all arguments *must* be keyword arguments in order to not
        break the application on upgrades.

        :param path:
            Rule strings basically are just normal URL paths with placeholders
            in the format ``<converter(arguments):name>`` where the converter
            and the arguments are optional. If no converter is defined the
            `default` converter is used which means `string` in the normal
            configuration.

            URL rules that end with a slash are branch URLs, others are leaves.
            If you have `strict_slashes` enabled (which is the default), all
            branch URLs that are matched without a trailing slash will trigger a
            redirect to the same URL with the missing slash appended.

            The converters are defined on the `Map`.
        :param name:
            The rule name used for URL generation.
        :param handler:
            The handler class used to handle requests when this rule matches.
            Can be a class or a class defined as a string to be lazily
            imported.
        :param defaults:
            An optional dict with defaults for other rules with the same
            endpoint. This is a bit tricky but useful if you want to have
            unique URLs::

                rules = [
                    Rule('/all/', name='pages', handler='handlers.PageHandler', defaults={'page': 1}),
                    Rule('/all/page/<int:page>', name='pages', handler='handlers.PageHandler'),
                ]

            If a user now visits ``http://example.com/all/page/1`` he will be
            redirected to ``http://example.com/all/``. If `redirect_defaults`
            is disabled on the `Map` instance this will only affect the URL
            generation.
        :param subdomain:
            The subdomain rule string for this rule. If not specified the rule
            only matches for the `default_subdomain` of the map. If the map is
            not bound to a subdomain this feature is disabled.

            Can be useful if you want to have user profiles on different
            subdomains and all subdomains are forwarded to your application.
        :param methods:
            A sequence of http methods this rule applies to. If not specified,
            all methods are allowed. For example this can be useful if you want
            different endpoints for `POST` and `GET`. If methods are defined
            and the path matches but the method matched against is not in this
            list or in the list of another rule for that path the error raised
            is of the type `MethodNotAllowed` rather than `NotFound`. If `GET`
            is present in the list of methods and `HEAD` is not, `HEAD` is
            added automatically.
        :param strict_slashes:
            Override the `Map` setting for `strict_slashes` only for this rule.
            If not specified the `Map` setting is used.
        :param build_only:
            Set this to True and the rule will never match but will create a
            URL that can be build. This is useful if you have resources on a
            subdomain or folder that are not handled by the WSGI application
            (like static data).
        :param redirect_to:
            If given this must be either a string or callable. In case of a
            callable it's called with the url adapter that triggered the match
            and the values of the URL as keyword arguments and has to return
            the target for the redirect, otherwise it has to be a string with
            placeholders in rule syntax::

                def foo_with_slug(adapter, id):
                    # ask the database for the slug for the old id. this of
                    # course has nothing to do with werkzeug.
                    return 'foo/' + Foo.get_slug_for_id(id)

                rules = [
                    Rule('/foo/<slug>', name='foo', handler='handlers.FooHandler'),
                    Rule('/some/old/url/<slug>', redirect_to='foo/<slug>'),
                    Rule('/other/old/url/<int:id>', redirect_to=foo_with_slug)
                ]

            When the rule is matched the routing system will raise a
            `RequestRedirect` exception with the target for the redirect.

            Keep in mind that the URL will be joined against the URL root of
            the script so don't use a leading slash on the target URL unless
            you really mean root of that domain.
        """
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

        return Rule(self.rule, name=self.name, handler=self.handler,
            defaults=defaults, subdomain=self.subdomain, methods=self.methods,
            build_only=self.build_only, strict_slashes=self.strict_slashes,
            redirect_to=self.redirect_to)


class HandlerPrefix(RuleFactory):
    """Prefixes all handler values of nested rules with another string. For
    example, take these rules::

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


class NamePrefix(RuleFactory):
    """Prefixes all name values of nested rules with another string. For
    example, take these rules::

        rules = [
            Rule('/', name='company-home', handler='handlers.HomeHandler'),
            Rule('/about', name='company-about', handler='handlers.AboutHandler'),
            Rule('/contact', name='company-contact', handler='handlers.ContactHandler'),
        ]

    You can wrap them by ``NamePrefix`` to define the name avoid repetition.
    This is equivalent to the above::

        rules = [
            NamePrefix('company-', [
                Rule('/', name='home', handler='handlers.HomeHandler'),
                Rule('/about', name='about', handler='handlers.AboutHandler'),
                Rule('/contact', name='contact', handler='handlers.ContactHandler'),
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
                rule.name = rule.endpoint = self.prefix + rule.name
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
