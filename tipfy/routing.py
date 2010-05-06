# -*- coding: utf-8 -*-
"""
    tipfy.routing
    ~~~~~~~~~~~~~

    URL routing utilities built on top of ``werkzeug.routing``.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from werkzeug.routing import BaseConverter, Map, Rule as WerkzeugRule

from tipfy import local


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
        WerkzeugRule.__init__(self, *args, **kwargs)

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


def url_for(endpoint, full=False, method=None, **kwargs):
    """Builds and returns a URL for a named :class:`Rule`.

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


Map.default_converters = dict(Map.default_converters)
Map.default_converters['regex'] = RegexConverter


__all__ = ['Rule',
           'url_for']
