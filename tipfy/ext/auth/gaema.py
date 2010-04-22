# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth.gaema
    ~~~~~~~~~~~~~~~~~~~~

    Authentication handler for `gaema`.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import datetime
import functools
import logging

from tipfy import local, HTTPException, RequestRedirect


class RequestAdapter(object):
    """Adapter to transform a `werkzeug.Request` object into a request with the
    attributes expected by `gaema`.

    It must define at least the following attributes or functions:

        request.arguments: a dictionary of GET parameters mapping to a list
                           of values.
        request.host: current request host.
        request.path: current request path.
        request.full_url(): a function returning the current full URL.
    """
    def __init__(self, request):
        """Initializes the request adapter.

        :param request:
            A `werkzeug.Request` instance.
        """
        self.arguments = dict(request.args)
        self.full_url = lambda: request.url
        self.host = request.host
        self.path = request.path


class AuthHandler(object):
    """Base authentication handler with common functions used by `gaema` mixin
    classes.
    """
    def __init__(self, request, **kwargs):
        """Depending on the auth mixins used, provide these configurations as
        keyword arguments:

        'google_consumer_key'
        'google_consumer_secret'

        'twitter_consumer_key'
        'twitter_consumer_secret'

        'friendfeed_consumer_key'
        'friendfeed_consumer_secret'

        'facebook_api_key'
        'facebook_secret'
        """
        self.request = RequestAdapter(request)
        self.settings = kwargs

    def require_setting(name, feature="this feature"):
        """Raises an exception if the given setting is not defined.

        :param name:
            Setting name.
        :param feature:
            Setting description.
        :return:
            `None`.
        """
        if not self.settings.get(name):
            raise Exception("You must define the '%s' setting in your "
                        "application to use %s" % (name, feature))

    def async_callback(self, callback, *args, **kwargs):
        """Wraps callbacks with this if they are used on asynchronous requests.

        Catches exceptions and properly finishes the request.

        :param callback:
            Callback function to be wrapped.
        :param args:
            Positional arguments fpr the callback.
        :param kwargs:
            Keyword arguments fpr the callback.
        :return:
            A wrapped callback.
        """
        if callback is None:
            return None

        if args or kwargs:
            callback = functools.partial(callback, *args, **kwargs)

        def wrapper(*args, **kwargs):
            try:
                return callback(*args, **kwargs)
            except Exception, e:
                logging.error('Exception during callback', exc_info=True)

        return wrapper

    def redirect(self, url):
        """Redirects to the given URL. We raise a `RequestRedirect`
        exception to be caught by the WSGI app.

        :param url:
            URL to redirect.
        :return:
            `None`.
        """
        raise RequestRedirect(url)

    _ARG_DEFAULT = []

    def get_argument(self, name, default=_ARG_DEFAULT, strip=True):
        """Returns the value of a request GET argument with the given name.

        If default is not provided, the argument is considered to be
        required, and we throw an HTTP 404 exception if it is missing.

        The returned value is always unicode.

        :param:
            Argument name to be retrieved from the request GET.
        :param default:
            Default value to be return if the argument is not in GET.
        :param strip:
            If `True`, returns the value after calling strip() on it.
        :return:
            A request argument, as unicode.
        """
        values = local.request.args.get(name, default)
        if value == _ARG_DEFAULT:
            raise HTTPException('Missing request argument %s' % name)

        if strip:
            value = value.strip()

        return value

    def get_cookie(self, name, default=None):
        """Gets the value of the cookie with the given name, else default.

        :param:
            Cookie name to be retrieved.
        :param default:
            Default value to be return if cookie is not set.
        :return:
            The cookie value.
        """
        return local.request.cookies.get(name, default)

    def set_cookie(self, name, value, domain=None, expires=None, path="/",
                   expires_days=None):
        """Sets the given cookie name/value with the given options.

        :param name:
            Cookie name.
        :param value:
            Cookie value.
        :param domain:
            Cookie domain.
        :param expires:
            A expiration date as a `datetime` object.
        :param path:
            Cookie path.
        :param expires_days:
            Number of days to calculate expiration.
        :return:
            `None`.
        """
        if expires_days is not None and not expires:
            expires = datetime.datetime.utcnow() + datetime.timedelta(
                days=expires_days)

        local.session_store.set_cookie(name, value, domain=domain, path=path,
            expires=expires)
