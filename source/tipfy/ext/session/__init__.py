# -*- coding: utf-8 -*-
"""
    tipfy.ext.session
    ~~~~~~~~~~~~~~~~~

    Session extension.

    This module provides sessions using secure cookies or the datastore.

    .. note::
       The session implementations are still pretty new and untested.
       Consider this as a work in progress.

    This module derives from `Kay`_.

    :copyright: (c) 2009 Accense Technology, Inc. All rights reserved.
    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import local, get_config, REQUIRED_CONFIG
from werkzeug.contrib.securecookie import SecureCookie

#: Default configuration values for this module. Keys are:
#: A dictionary of configuration options for ``tipfy.ext.session``. Keys are:
#:   - ``secret_key``: Secret key to generate session cookies. Set this to
#:     something random and unguessable. Default is
#:     :data:`tipfy.REQUIRED_CONFIG` (an exception is raised if it is not set).
#:   - ``expiration``: Session expiration time in seconds. Default is `86400`.
#:   - ``cookie_name``: Name of the cookie to save the session. Default is
#:     `tipfy.session`.
#:   - ``id_cookie_name``:Name of the cookie to save the session id. Default is
#:     `tipfy.session_id`.
default_config = {
    'secret_key': REQUIRED_CONFIG,
    'expiration': 86400,
    'cookie_name': 'tipfy.session',
    'id_cookie_name': 'tipfy.session_id',
}

# Proxies to the session variables set on each request.
local.session = local.session_store = None
session, session_store = local('session'), local('session_store')


def get_secure_cookie(key=None, data=None):
    """Loads a `SecureCookie` from a cookie, or creates a new one.

    :param key:
        Secure cookie key. If not provided, simply returns a new `SecureCookie`.
        If the key is provided and the cookie is not set,also returns a new
        `SecureCookie` instance.
    :return:
        A SecureCookie instance.
    """
    secret_key = get_config(__name__, 'secret_key')

    if key is None:
        cookie = SecureCookie(data=data, secret_key=secret_key)
    else:
        cookie = SecureCookie.load_cookie(local.request, key=key, secret_key=
            secret_key)

        if data is not None:
            cookie.update(data)

    if data is not None:
        # Always force it to save when data is passed.
        cookie.modified = True

    return cookie


def set_secure_cookie(key, data=None, cookie=None, **kwargs):
    """Sets a cookie that is not alterable from the client.

    :param key:
        Secure cookie key.
    :param data:
        Dictionary of values to be saved in a new cookie.
    :param cookie:
        A `SecureCookie` instance to save the data instead of creating a new
        one.
    :param kwargs:
        Keyword arguments used to store the cookie. Check
        `SecureCookie.save_cookie()` for a description or the arguments.
    :return:
        `None`.
    """
    if cookie is None:
        cookie = SecureCookie(data=data, secret_key=get_config(__name__,
            'secret_key'))
    elif data is not None:
        cookie.update(data)

    if data is not None:
        # Always force it to save when data is passed.
        cookie.modified = True

    cookie.save_cookie(local.response, key=key, **kwargs)
