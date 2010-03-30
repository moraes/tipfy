# -*- coding: utf-8 -*-
"""
    tipfy.utils
    ~~~~~~~~~~~

    Miscelaneous utilities.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import import_string, redirect, Response, url_for


def redirect_to(endpoint, method=None, code=302, **kwargs):
    """Convenience function mixing :func:`redirect` and :func:`url_for`:
    redirects the client to a URL built using a named :class:`Rule`.

    :param endpoint:
        The rule endpoint.
    :param method:
        The rule request method, in case there are different rules
        for different request methods.
    :param code:
        The redirect status code.
    :param kwargs:
        Keyword arguments to build the URL.
    :return:
        A ``werkzeug.Response`` object with headers set for redirection.
    """
    return redirect(url_for(endpoint, full=True, method=method, **kwargs),
        code=code)


def render_json_response(obj):
    """Renders a JSON response, automatically encoding `obj` to JSON.

    :param obj:
        An object to be serialized to JSON, normally a dictionary.
    :return:
        A ``werkzeug.Response`` object with `obj` converted to JSON in the body
        and mimetype set to ``application/json``.
    """
    from django.utils import simplejson
    return Response(simplejson.dumps(obj), mimetype='application/json')


def normalize_callable(spec):
    """Many `Tipfy`_ configurations expect a callable or optionally a string
    with a callable definition to be lazily imported. This function normalizes
    those definitions, importing the callable if necessary.

    :param spec:
        A callable or a string with a callable definition to be imported.
    :return:
        A callable.
    """
    if isinstance(spec, basestring):
        spec = import_string(spec)

    if not callable(spec):
        raise ValueError('%s is not a callable.' % str(spec))

    return spec


__all__ = ['normalize_callable',
           'redirect_to',
           'render_json_response']
