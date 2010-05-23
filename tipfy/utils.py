# -*- coding: utf-8 -*-
"""
    tipfy.utils
    ~~~~~~~~~~~

    Miscelaneous utilities.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import import_string, redirect, Response, url_for


def redirect_to(endpoint, _method=None, _anchor=None, _code=302, **kwargs):
    """Convenience function mixing :func:`redirect` and :func:`url_for`:
    redirects the client to a URL built using a named :class:`Rule`.

    :param endpoint:
        The rule endpoint.
    :param _method:
        The rule request method, in case there are different rules
        for different request methods.
    :param _anchor:
        An anchor to add to the end of the URL.
    :param _code:
        The redirect status code.
    :param kwargs:
        Keyword arguments to build the URL.
    :return:
        A :class:`tipfy.Response` object with headers set for redirection.
    """
    # For backwards compatibility, check old keywords.
    method = kwargs.pop('method', _method)
    code = kwargs.pop('code', _code)

    url = url_for(endpoint, _full=True, _method=method, _anchor=_anchor,
        **kwargs)
    return redirect(url, code=code)


def render_json_response(*args, **kwargs):
    """Renders a JSON response, automatically encoding `obj` to JSON.

    :param args:
        Arguments to be passed to simplejson.dumps().
    :param kwargs:
        Keyword arguments to be passed to simplejson.dumps().
    :return:
        A :class:`tipfy.Response` object with `obj` converted to JSON in
        the body and mimetype set to ``application/json``.
    """
    from django.utils import simplejson
    return Response(simplejson.dumps(*args, **kwargs),
        mimetype='application/json')


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
