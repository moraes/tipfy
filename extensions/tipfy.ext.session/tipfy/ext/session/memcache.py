# -*- coding: utf-8 -*-
"""
    tipfy.ext.session.memcache
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Memcache-based sessions.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from google.appengine.api import memcache

from tipfy.ext.session import SessionStore


class MemcacheSessionStore(SessionStore):
    @property
    def namespace(self):
        """Returns the namespace to be used in memcache.

        :return:
            A namespace string.
        """
        return MemcacheSessionStore.get_namespace()

    @classmethod
    def get_namespace(cls):
        """Returns the namespace to be used in memcache.

        :return:
            A namespace string.
        """
        return cls.__module__ + '.' + cls.__name__

    def save(self, session):
        """Saves a session."""
        memcache.set(session.sid, dict(session), namespace=self.namespace)

    def delete(self, session):
        """Deletes a session."""
        memcache.delete(session.sid, namespace=self.namespace)

    def get(self, sid=None):
        """Returns a session given a session id."""
        if not sid or not self.is_valid_key(sid):
            return self.new()

        data = memcache.get(sid, namespace=self.namespace)
        if not data:
            return self.new()

        return self.session_class(data, sid, False)

    def get_and_delete(self, sid=None):
        """Returns a session, deleting it after it is loaded."""
        session = self.get(sid)
        if not session.new:
            self.delete(session)

        return session


class MemcacheSessionMiddleware(object):
    pass
