# -*- coding: utf-8 -*-
"""
    tipfy.ext.session
    ~~~~~~~~~~~~~~~~~

    Session extension.

    This module provides sessions using secure cookies, memcache or datastore.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from werkzeug.contrib.sessions import (Session,
    SessionStore as BaseSessionStore, generate_key)
from werkzeug.security import gen_salt


class SessionStore(BaseSessionStore):
    session_class = Session

    def __init__(self, session_class=None):
        BaseSessionStore.__init__(self, session_class=session_class or
            self.session_class)

    def generate_key(self, salt=None):
        """Returns a new session key."""
        return generate_key(salt or gen_salt(10))
