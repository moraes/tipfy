# -*- coding: utf-8 -*-
"""
    tipfy.utils
    ~~~~~~~~~~~

    Miscelaneous utilities.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import werkzeug

import tipfy
from tipfy import routing


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
        A ``werkzeug.Response`` object with headers set for redirection.
    """
    response = getattr(tipfy.local, 'response', None)
    if response is None:
        response = werkzeug.Response()

    assert code in (301, 302, 303, 305, 307), 'invalid code'
    response.data = \
        '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n' \
        '<title>Redirecting...</title>\n' \
        '<h1>Redirecting...</h1>\n' \
        '<p>You should be redirected automatically to target URL: ' \
        '<a href="%s">%s</a>.  If not click the link.' % \
        ((werkzeug.escape(location),) * 2)
    response.status_code = code
    response.headers['Location'] = location
    return response


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
    return redirect(routing.url_for(endpoint, full=True, method=method,
        **kwargs), code=code)


def render_json_response(obj):
    """Renders a JSON response, automatically encoding `obj` to JSON.

    :param obj:
        An object to be serialized to JSON, normally a dictionary.
    :return:
        A ``werkzeug.Response`` object with `obj` converted to JSON in the body
        and mimetype set to ``application/json``.
    """
    response = getattr(tipfy.local, 'response', None)
    if response is None:
        response = werkzeug.Response()

    from django.utils import simplejson
    response.data = simplejson.dumps(obj)
    response.mimetype = 'application/json'
    return response


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
        spec = werkzeug.import_string(spec)

    if not callable(spec):
        raise ValueError('%s is not a callable.' % str(spec))

    return spec


__all__ = ['normalize_callable', 'redirect', 'redirect_to',
    'render_json_response']
