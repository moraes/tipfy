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

from tipfy import local, app, get_config

# Let other modules initialize sessions.
is_session_set = False
# The module name from where we get configuration values.
EXT = 'tipfy.ext.session'


def setup():
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
    global is_session_set
    if is_session_set is False:
        middleware = SecureCookieSessionMiddleware()
        app.hooks.add('pre_dispatch_handler', middleware.load_session)
        app.hooks.add('pre_send_response', middleware.save_session)
        is_session_set = True


class SecureCookieSessionMiddleware(object):
    """Enables sessions using secure cookies."""
    def __init__(self):
        self.session_store = SecureCookieSessionStore(get_config(EXT,
            'cookie_name'))

    def load_session(self):
        local.session_store = self.session_store
        local.session = self.session_store.get(None)

    def save_session(self, request=None, response=None, app=None):
        if hasattr(local, 'session'):
            self.session_store.save_if_modified(local.session)

        return response


class SecureCookieSessionStore(SessionStore):
    """A session store class that stores data in secure cookies."""
    def __init__(self, cookie_name, expires=None):
        self.cookie_name = cookie_name
        self.secret_key = get_config(EXT, 'secret_key')
        self.expires = expires or get_config(EXT, 'expiration')

    def new(self):
        return self.get(None)

    def get(self, sid):
        return SecureCookie.load_cookie(local.request, key=self.cookie_name,
            secret_key=self.secret_key)

    def save(self, session):
        session.save_cookie(local.response, key=self.cookie_name, expires=
            datetime.now() + timedelta(seconds=self.expires))

    def delete(self, session):
        for key in session.keys():
            del session[key]
