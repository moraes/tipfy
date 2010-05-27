# -*- coding: utf-8 -*-
"""
    tipfy.routing
    ~~~~~~~~~~~~~

    URL routing utilities built on top of ``werkzeug.routing``.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from werkzeug.routing import BaseConverter, Map, Rule as WerkzeugRule

from tipfy import Tipfy


class Rule(WerkzeugRule):
    """Extends Werkzeug routing to support a handler definition for each Rule.
    Handler is a :class:`RequestHandler` module and class specification, and
    endpoint is a friendly name used to build URL's. For example:

    .. code-block:: python

       Rule('/users', endpoint='user-list', handler='my_app:UsersHandler')

    Access to the URL ``/users`` loads ``UsersHandler`` class from ``my_app``
    module. To generate a URL to that page, use :func:`url_for`:

    .. code-block:: python

       url = url_for('user-list')

    """
    def __init__(self, *args, **kwargs):
        self.handler = kwargs.pop('handler', kwargs.get('endpoint', None))
        super(Rule, self).__init__(*args, **kwargs)

    def empty(self):
        """Returns an unbound copy of this rule. This can be useful if you
        want to reuse an already bound URL for another map.
        """
        defaults = None
        if self.defaults is not None:
            defaults = dict(self.defaults)
        return Rule(self.rule, defaults, self.subdomain, self.methods,
                    self.build_only, self.endpoint, self.strict_slashes,
                    self.redirect_to, handler=self.handler)


# Extra URL rule converter from
# http://groups.google.com/group/pocoo-libs/browse_thread/thread/ff5a3fddee12a955/
class RegexConverter(BaseConverter):
    """Matches a regular expression::

       Rule('/<regex(".*$"):name>')
    """
    def __init__(self, map, *items):
        BaseConverter.__init__(self, map)
        self.regex = items[0]


def url_for(endpoint, _full=False, _method=None, _anchor=None, **kwargs):
    """Builds and returns a URL for a named :class:`tipfy.Rule`.

    For example, if you have these rules registered in the application:

        Rule('/', endoint='home/main' handler='handlers.MyHomeHandler')
        Rule('/wiki', endoint='wiki/start' handler='handlers.WikiHandler')

    Here are some examples of how to generate URLs for them:

        >>> url = url_for('home/main')
        >>> '/'
        >>> url = url_for('home/main', _full=True)
        >>> 'http://localhost:8080/'
        >>> url = url_for('wiki/start')
        >>> '/wiki'
        >>> url = url_for('wiki/start', _full=True)
        >>> 'http://localhost:8080/wiki'
        >>> url = url_for('wiki/start', _full=True, _anchor='my-heading')
        >>> 'http://localhost:8080/wiki#my-heading'

    :param endpoint:
        The rule endpoint.
    :param _full:
        If True, returns an absolute URL. Otherwise, returns a relative
        one.
    :param _method:
        The rule request method, in case there are different rules
        for different request methods.
    :param _anchor:
        An anchor to add to the end of the URL.
    :param kwargs:
        Keyword arguments to build the URL.
    :return:
        An absolute or relative URL.
    """
    # For backwards compatibility, check old keywords.
    full = kwargs.pop('full', _full)
    method = kwargs.pop('method', _method)

    return Tipfy.request.url_for(endpoint, _full=full, _method=method,
        _anchor=_anchor, **kwargs)


Map.default_converters = dict(Map.default_converters)
Map.default_converters['regex'] = RegexConverter


__all__ = ['Rule',
           'url_for']
