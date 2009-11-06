# -*- coding: utf-8 -*-
"""
    tipfy.ext.sessions
    ~~~~~~~~~~~~~~~~~~

    Sessions extension.

    This file derives from Kay.

    :copyright: (c) 2009 Accense Technology, Inc. All rights reserved.
    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from werkzeug.contrib.securecookie import SecureCookie

from tipfy import local

NO_SESSION = 'nosession'


class SecureCookieSessionStore(object):
    """A session store class that stores data in secure cookies."""
    cookie_name = 'tipfy.session'

    def __init__(self):
        self.secret_key = local.app.config.session_secret_key

    def new(self):
        return SecureCookie.load_cookie(local.request, key=self.cookie_name,
            secret_key=self.secret_key)

    def get(self, data):
        return SecureCookie.unserialize(data, self.secret_key)

    def save(self, session):
        session.save_cookie(local.response, key=self.cookie_name)

    def get_data(self, session):
        return session.serialize()

    def delete(self, session):
        pass


class SessionMiddleware(object):
    store_class = SecureCookieSessionStore

    def __init__(self):
        self.session_store = self.store_class()

    def process_handler(self, request, handler, **kwargs):
        if hasattr(handler, NO_SESSION):
            return None

        request.session = self.session_store.new()
        return None

    def process_response(self, request, response):
        if hasattr(request, 'session') and request.session.should_save:
            self.session_store.save(request.session)

        return response
