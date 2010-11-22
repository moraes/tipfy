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

from tipfy.sessions import BaseSession

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


class AppEngineBaseSession(BaseSession):
    __slots__ = BaseSession.__slots__ + ('sid',)

    def __init__(self, data=None, sid=None, new=False):
        BaseSession.__init__(self, data, new)
        if new:
            self.sid = self.__class__._get_new_sid()
        elif sid is None:
            raise ValueError('A session id is required for existing sessions.')
        else:
            self.sid = sid

    @classmethod
    def _get_new_sid(cls):
        # Force a namespace in the key, to not pollute the namespace in case
        # global namespaces are in use.
        return cls.__module__ + '.' + cls.__name__ + '.' + uuid.uuid4().hex

    @classmethod
    def get_session(cls, store, name=None, **kwargs):
        if name:
            cookie = store.get_secure_cookie(name)
            if cookie is not None:
                sid = cookie.get('_sid')
                if sid and _is_valid_key(sid):
                    return cls._get_by_sid(sid, **kwargs)

        return cls(new=True)


class DatastoreSession(AppEngineBaseSession):
    """A session that stores data serialized in the datastore."""
    model_class = SessionModel

    @classmethod
    def _get_by_sid(cls, sid, **kwargs):
        """Returns a session given a session id."""
        entity = cls.model_class.get_by_sid(sid)
        if entity is not None:
            return cls(entity.data, sid)

        return cls(new=True)

    def save_session(self, response, store, name, **kwargs):
        if not self.modified:
            return

        self.model_class.create(self.sid, dict(self)).put()
        store.set_secure_cookie(response, name, {'_sid': self.sid}, **kwargs)


class MemcacheSession(AppEngineBaseSession):
    """A session that stores data serialized in memcache."""
    @classmethod
    def _get_by_sid(cls, sid, **kwargs):
        """Returns a session given a session id."""
        data = memcache.get(sid)
        if data is not None:
            return cls(data, sid)

        return cls(new=True)

    def save_session(self, response, store, name, **kwargs):
        if not self.modified:
            return

        memcache.set(self.sid, dict(self))
        store.set_secure_cookie(response, name, {'_sid': self.sid}, **kwargs)


def _is_valid_key(key):
    """Check if a session key has the correct format."""
    return _UUID_RE.match(key.split('.')[-1]) is not None
