# -*- coding: utf-8 -*-
"""
    tipfy.ext.session.securecookie
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Secure cookies session extension.

    This module derives from `Kay`_.

    :copyright: (c) 2009 Accense Technology, Inc. All rights reserved.
    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime, timedelta

from werkzeug.contrib.securecookie import SecureCookie
from werkzeug.contrib.sessions import SessionStore

from tipfy import local, get_config

# Let other modules initialize sessions.
_is_ext_set = False
# The module name from where we get configuration values.
EXT = 'tipfy.ext.session'


def setup(app):
    """
    Setup this extension.

    This will set hooks to initialize and persist securecookie based sessions.
    This initializes :class:`DatastoreSessionMiddleware` and sets hooks to load
    and save sessions.

    To enable it, add this module to the list of extensions in ``config.py``:

    .. code-block:: python

       config = {
           'tipfy': {
               'extensions': [
                   'tipfy.ext.session.securecookie',
                   # ...
               ],
           },
       }

    :return:
        ``None``.
    """
    global _is_ext_set
    if _is_ext_set is False:
        middleware = SecureCookieSessionMiddleware()
        app.hooks.add('pre_dispatch_handler', middleware.load_session)
        app.hooks.add('pre_send_response', middleware.save_session)
        _is_ext_set = True


class SecureCookieSessionMiddleware(object):
    """Enables sessions using secure cookies."""
    def __init__(self, cookie_name=None):
        if cookie_name is None:
            cookie_name = get_config(EXT, 'cookie_name')

        expires = get_config(EXT, 'expiration')
        self.session_store = SecureCookieSessionStore(cookie_name, expires)

    def load_session(self, app, request):
        local.session_store = self.session_store
        local.session = self.session_store.get(None)

    def save_session(self, app, request, response):
        if hasattr(local, 'session'):
            self.session_store.save_if_modified(local.session)


class SecureCookieSessionStore(SessionStore):
    """A session store class that stores data in secure cookies."""
    def __init__(self, cookie_name, session_expires=None, max_age=None,
        path='/', domain=None, secure=None, httponly=False, force=False):
        self.cookie_name = cookie_name
        self.session_expires = session_expires
        self.max_age = max_age
        self.path = path
        self.domain = domain
        self.secure = secure
        self.httponly = httponly
        self.force = force
        self.secret_key = get_config(EXT, 'secret_key')

    def new(self):
        return self.get(None)

    def get(self, sid=None):
        key = sid or self.cookie_name
        return SecureCookie.load_cookie(local.request, key=key,
            secret_key=self.secret_key)

    def save(self, session):
        session.save_cookie(local.response, key=self.cookie_name,
            max_age=self.max_age)

    def delete(self, session):
        for key in session.keys():
            del session[key]
