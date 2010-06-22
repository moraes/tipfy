# -*- coding: utf-8 -*-
"""
    tipfy.ext.session.datastore
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Datastore-based sessions.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime, timedelta

from google.appengine.api import memcache
from google.appengine.ext import db

from werkzeug.contrib.sessions import Session as BaseSessionData

from tipfy import get_config
from tipfy.ext.db import (PickleProperty, get_protobuf_from_entity,
    get_entity_from_protobuf)
from tipfy.ext.session import SessionStore


#: Default configuration values for this module. Keys are:
#:
#: - ``session_max_age``: Session expiration time in seconds. Datastore
#:   entities older than this age will not be valid.
default_config = {
    'session_max_age': None,
}


class Session(db.Model):
    """Stores session data."""
    #: Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    #: Session data, pickled.
    data = PickleProperty()

    @property
    def sid(self):
        """Returns the session id, which is the same as the key name.

        :return:
            A session unique id.
        """
        return self.key().name()

    @property
    def valid(self):
        """Returns ``True`` if the session has not expired.

        :return:
            ``True`` if the session has not expired, ``False`` otherwise.
        """
        seconds = get_config(__name__, 'session_max_age')
        if not seconds:
            return True

        return self.created + timedelta(seconds=seconds) < datetime.now()

    @property
    def namespace(self):
        """Returns the namespace to be used in memcache.

        :return:
            A namespace string.
        """
        return Session.get_namespace()

    @classmethod
    def get_namespace(cls):
        """Returns the namespace to be used in memcache.

        :return:
            A namespace string.
        """
        return cls.__module__ + '.' + cls.__name__

    @classmethod
    def get_by_sid(cls, sid):
        """Returns a ``Session`` instance by session id.

        :param sid:
            A session id.
        :return:
            An existing ``Session`` entity.
        """
        data = cls.get_cache(sid)
        if data:
            session = get_entity_from_protobuf(data)
        else:
            session = Session.get_by_key_name(sid)
            if session:
                session.set_cache()

        if session and not session.valid:
            return None

        return session

    @classmethod
    def create(cls, sid, data=None):
        """Returns a new, empty session entity.

        :param sid:
            A session id.
        :return:
            A new and not saved session entity.
        """
        return cls(key_name=sid, data=data or {})

    @classmethod
    def get_cache(cls, sid):
        return memcache.get(sid, namespace=cls.get_namespace())

    def set_cache(self):
        """Saves a new cache for this entity."""
        memcache.set(self.sid, get_protobuf_from_entity(self),
            namespace=self.namespace)

    def delete_cache(self):
        """Saves a new cache for this entity."""
        memcache.delete(self.sid, namespace=self.namespace)

    def put(self):
        """Saves the session and updates the memcache entry."""
        self.set_cache()
        db.put(self)

    def delete(self):
        """Deletes the session and the memcache entry."""
        self.delete_cache()
        db.delete(self)


class SessionData(BaseSessionData):
    __slots__ = BaseSessionData.__slots__ + ('entity',)

    def __init__(self, data, sid, new=False, entity=None):
        BaseSessionData.__init__(self, data, sid, new)
        self.entity = entity


class DatastoreSessionStore(SessionStore):
    model_class = Session
    session_class = SessionData

    def save(self, session):
        """Saves a session."""
        session.entity = self.model_class.create(session.sid, dict(session))
        session.entity.put()

    def delete(self, session):
        """Deletes a session."""
        if session.entity and session.entity.is_saved():
            session.entity.delete()

    def get(self, sid=None):
        """Returns a session given a session id."""
        if not sid or not self.is_valid_key(sid):
            return self.new()

        entity = self.model_class.get_by_sid(sid)
        if not entity:
            return self.new()

        return self.session_class(entity.data, sid, False, entity)

    def get_and_delete(self, sid=None):
        """Returns a session, deleting it after it is loaded."""
        session = self.get(sid)
        if not session.new:
            self.delete(session)

        return session


class DatastoreSessionMiddleware(object):
    pass
