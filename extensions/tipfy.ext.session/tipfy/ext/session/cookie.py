# -*- coding: utf-8 -*-
"""
    tipfy.ext.session.cookie
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Securecookie-based sessions.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from werkzeug.contrib.securecookie import SecureCookie

from tipfy.ext.session import SessionStore


class CookieSessionStore(SessionStore):
    session_class = SecureCookie

    def save(self, session, response):
        """Saves a session."""

    def delete(self, session, response):
        """Deletes a session."""

    def get(self, key, request):
        """Returns a session given a session id."""

    def get_and_delete(self, key, request, response):
        """Returns a session, deleting it after it is loaded."""
