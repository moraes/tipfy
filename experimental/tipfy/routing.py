from werkzeug import import_string, url_quote
from werkzeug.routing import BaseConverter, Map, Rule as BaseRule, RuleFactory


class Router(object):
    def __init__(self, app, rules=None):
        """
        :param app:
            A :class:`Tipfy` instance.
        :param rules:
            Initial URL rules definitions. It can be a list of :class:`Rule`,
            a callable or a string defining a callable that returns the rules
            list. The callable is called passing the WSGI application as
            parameter. If None, it will import ``get_rules()`` from *urls.py*
            and call it passing the WSGI application.
        """
        self.app = app
        self.handlers = {}
        self.map = self.get_map(rules)

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
        """Matches registered :class:`Rule` definitions against the URL
        adapter. This will store the URL adapter, matched rule and rule
        arguments in the :class:`Request` instance.

        Three exceptions can occur when matching the rules: ``NotFound``,
        ``MethodNotAllowed`` or ``RequestRedirect``. If they are
        raised, they are stored in the request for later use.

        :param request:
            A :class:`Request` instance.
        :returns:
            None.
        """
        # Bind the URL map to the current request
        request.url_adapter = self.map.bind_to_environ(request.environ,
            server_name=self.get_server_name())

        # Match the path against registered rules.
        match = request.url_adapter.match(return_rule=True)
        request.rule, request.rule_args = match
        return match

    def dispatch(self, app, request, match, method=None):
        """Dispatches a request. This calls the :class:`RequestHandler` from
        the matched :class:`Rule`.

        :param app:
            A :class:`Tipfy` instance.
        :param request:
            A :class:`Request` instance.
        :param match:
            A tuple ``(rule, kwargs)``, resulted from the matched URL.
        :param method:
            Handler method to be called. In cases like exception handling, a
            method can be forced instead of using the request method.
        """
        method = method or request.method.lower().replace('-', '_')
        rule, kwargs = match

        if isinstance(rule.handler, basestring):
            if rule.handler not in self.handlers:
                # Import handler set in matched rule. This can raise an
                # ImportError or AttributeError if the handler is badly
                # defined. The exception will be caught in the WSGI app.
                self.handlers[rule.handler] = import_string(rule.handler)

            rule.handler = self.handlers[rule.handler]

        # Instantiate handler.
        handler = rule.handler(app, request)
        try:
            # Dispatch the requested method.
            return handler(method, **kwargs)
        except Exception, e:
            if method == 'handle_exception':
                # We are already handling an exception.
                raise

            # If the handler implements exception handling, let it handle it.
            return handler.handle_exception(exception=e)

    def build(self, request, name, kwargs):
        """Returns a URL for a named :class:`Rule`. This is the central place
        to build URLs for an app. It is used by :meth:`RequestHandler.url_for`,
        :meth:`Tipfy.url_for and the standalone function :func:`url_for`.
        Those functions conveniently pass the current request object so you
        don't have to.

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

    def get_server_name(self):
        """Returns the server name used to bind the URL map. By default it
        returns the configured server name. Extend this if you want to
        calculate the server name dynamically (e.g., to match subdomains
        from multiple domains).

        :returns:
            The server name used to build the URL adapter.
        """
        return self.app.config.get('tipfy', 'server_name')

    def get_default_subdomain(self):
        """Returns the default subdomain for rules without a subdomain
        defined. By default it returns the configured default subdomain.

        :returns:
            The default subdomain to be used in the URL map.
        """
        return self.app.config.get('tipfy', 'default_subdomain')

    def get_map(self, rules=None):
        """Returns a ``werkzeug.routing.Map`` instance with the given
        :class:`Rule` definitions.

        :param rules:
            A list of :class:`Rule` definitions.
        :returns:
            A ``werkzeug.routing.Map`` instance.
        """
        return Map(rules, default_subdomain=self.get_default_subdomain())


class Rule(BaseRule):
    """Extends Werkzeug routing to support handler and name definitions for
    each Rule. Handler is a :class:`RequestHandler` class and name is a
    friendly name used to build URL's. For example:

    .. code-block:: python

        Rule('/users', name='user-list', handler='my_app:UsersHandler')

    Access to the URL ``/users`` loads ``UsersHandler`` class from
    ``my_app`` module. To generate a URL to that page, use :func:`url_for`::

        url = url_for('user-list')
    """
    def __init__(self, path, handler=None, name=None, **kwargs):
        self.name = kwargs.pop('endpoint', name)
        self.handler = handler or self.name
        super(Rule, self).__init__(path, endpoint=self.name, **kwargs)

    def empty(self):
        """Returns an unbound copy of this rule. This can be useful if you
        want to reuse an already bound URL for another map.
        """
        defaults = None
        if self.defaults is not None:
            defaults = dict(self.defaults)

        return Rule(self.rule, handler=self.handler, name=self.endpoint,
            defaults=defaults, subdomain=self.subdomain, methods=self.methods,
            build_only=self.build_only, strict_slashes=self.strict_slashes,
            redirect_to=self.redirect_to)


class HandlerPrefix(RuleFactory):
    """Prefixes all handler values (which must be strings for this factory) of
    nested rules with another string. For example, take these rules::

        rules = [
            Rule('/', name='index', handler='my_app.handlers.IndexHandler'),
            Rule('/entry/<entry_slug>', name='show', handler='my_app.handlers.ShowHandler'),
        ]

    You can wrap them by ``HandlerPrefix`` to define the handler module and
    avoid repetition. This is equivalent to the above::

        rules = [
            HandlerPrefix('my_app.handlers.', [
                Rule('/', name='index', handler='IndexHandler'),
                Rule('/entry/<entry_slug>', name='show', handler='ShowHandler'),
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
    """A :class: `Rule` converter that matches a regular expression::

        Rule(r'/<regex(".*$"):name>')
    """
    def __init__(self, map, *items):
        BaseConverter.__init__(self, map)
        self.regex = items[0]


# Add regex converter to the list of converters.
Map.default_converters = dict(Map.default_converters)
Map.default_converters['regex'] = RegexConverter
