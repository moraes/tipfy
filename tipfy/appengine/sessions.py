# -*- coding: utf-8 -*-
"""
    tipfy.appengine.sessions
    ~~~~~~~~~~~~~~~~~~~~~~~~

    App Engine session backends.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import re
import uuid

from google.appengine.api import memcache
from google.appengine.ext import db

from tipfy.config import DEFAULT_VALUE
from tipfy.sessions import BaseSessionFactory, SessionDict
from tipfy.appengine.db import (PickleProperty, get_protobuf_from_entity,
    get_entity_from_protobuf)

# Validate session keys.
_UUID_RE = re.compile(r'^[a-f0-9]{32}$')


class SessionModel(db.Model):
    """Stores session data."""
    kind_name = 'Session'

    #: Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    #: Session data, pickled.
    data = PickleProperty()

    @property
    def sid(self):
        """Returns the session id, which is the same as the key name.

        :returns:
            A session unique id.
        """
        return self.key().name()

    @classmethod
    def kind(cls):
        """Returns the datastore kind we use for this model."""
        return cls.kind_name

    @classmethod
    def get_by_sid(cls, sid):
        """Returns a ``Session`` instance by session id.

        :param sid:
            A session id.
        :returns:
            An existing ``Session`` entity.
        """
        session = cls.get_cache(sid)
        if not session:
            session = SessionModel.get_by_key_name(sid)
            if session:
                session.set_cache()

        return session

    @classmethod
    def create(cls, sid, data=None):
        """Returns a new, empty session entity.

        :param sid:
            A session id.
        :returns:
            A new and not saved session entity.
        """
        return cls(key_name=sid, data=data or {})

    @classmethod
    def get_cache(cls, sid):
        data = memcache.get(sid)
        if data:
            return get_entity_from_protobuf(data)

    def set_cache(self):
        """Saves a new cache for this entity."""
        memcache.set(self.sid, get_protobuf_from_entity(self))

    def delete_cache(self):
        """Saves a new cache for this entity."""
        memcache.delete(self.sid)

    def put(self):
        """Saves the session and updates the memcache entry."""
        self.set_cache()
        db.put(self)

    def delete(self):
        """Deletes the session and the memcache entry."""
        self.delete_cache()
        db.delete(self)


class AppEngineSessionFactory(BaseSessionFactory):
    session_class = SessionDict
    sid = None

    def get_session(self, max_age=DEFAULT_VALUE):
        if self.session is None:
            data = self.session_store.get_secure_cookie(self.name,
                                                        max_age=max_age)
            if data is not None:
                self.sid = data.get('_sid')
                if _is_valid_key(self.sid):
                    self.session = self._get_by_sid(self.sid)

            if self.session is None:
                self.sid = self._get_new_sid()
                self.session = self.session_class(self, new=True)

        return self.session

    def _get_new_sid(self):
        return uuid.uuid4().hex


class DatastoreSessionFactory(AppEngineSessionFactory):
    model_class = SessionModel

    def _get_by_sid(self, sid):
        """Returns a session given a session id."""
        entity = self.model_class.get_by_sid(sid)
        if entity is not None:
            return self.session_class(self, data=entity.data)

        self.sid = self._get_new_sid()
        return self.session_class(self, new=True)

    def save_session(self, response):
        if self.session is None or not self.session.modified:
            return

        self.model_class.create(self.sid, dict(self.session)).put()
        self.session_store.set_secure_cookie(
            response, self.name, {'_sid': self.sid}, **self.session_args)


class MemcacheSessionFactory(AppEngineSessionFactory):
    """A session that stores data serialized in memcache."""
    def _get_by_sid(self, sid):
        """Returns a session given a session id."""
        data = memcache.get(sid)
        if data is not None:
            return self.session_class(self, data=data)

        self.sid = self._get_new_sid()
        return self.session_class(self, new=True)

    def save_session(self, response):
        if self.session is None or not self.session.modified:
            return

        memcache.set(self.sid, dict(self.session))
        self.session_store.set_secure_cookie(
            response, self.name, {'_sid': self.sid}, **self.session_args)


def _is_valid_key(key):
    """Check if a session key has the correct format."""
    if not key:
        return False

    return _UUID_RE.match(key.split('.')[-1]) is not None
