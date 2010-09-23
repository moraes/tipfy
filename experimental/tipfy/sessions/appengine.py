# -*- coding: utf-8 -*-
"""
    tipfy.sessions.appengine
    ~~~~~~~~~~~~~~~~~~~~~~~~

    App Engine session backends.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import re
import uuid

from google.appengine.api import memcache
from google.appengine.ext import db

from werkzeug.contrib.sessions import ModificationTrackingDict

from tipfyext.appengine.db import (PickleProperty, get_protobuf_from_entity,
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

    @classmethod
    def kind(cls):
        """Returns the datastore kind we use for this model.
        """
        return cls.kind_name

    @property
    def sid(self):
        """Returns the session id, which is the same as the key name.

        :returns:
            A session unique id.
        """
        return self.key().name()

    @classmethod
    def get_by_sid(cls, sid):
        """Returns a ``Session`` instance by session id.

        :param sid:
            A session id.
        :returns:
            An existing ``Session`` entity.
        """
        data = cls.get_cache(sid)
        if data:
            session = get_entity_from_protobuf(data)
        else:
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
        return memcache.get(sid)

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


class _BaseSession(ModificationTrackingDict):
    __slots__ = ModificationTrackingDict.__slots__ + ('sid',)

    def __init__(self, data, sid, modified=False):
        ModificationTrackingDict.__init__(self, data)
        self.sid = sid
        self.modified = modified

    @classmethod
    def _get_new_sid(cls):
        # Force a namespace in the key, to not pollute the namespace in case
        # global namespaces are in use.
        return cls.__module__ + '.' + cls.__name__ + '.' + uuid.uuid4().hex

    @classmethod
    def get_session(cls, store, name, **kwargs):
        cookie = store.get_secure_cookie(name) or {}
        return cls._get_by_sid(cookie.get('_sid'), **kwargs)


class DatastoreSession(_BaseSession):
    model_class = SessionModel

    @classmethod
    def _get_by_sid(cls, sid, **kwargs):
        """Returns a session given a session id."""
        entity = None

        if sid and _is_valid_key(sid):
            entity = cls.model_class.get_by_sid(sid)

        if not entity:
            return cls((), cls._get_new_sid(), modified=True)

        return cls(entity.data, sid)

    def save_session(self, response, store, name, **kwargs):
        if not self or not self.modified:
            return

        self.entity = self.model_class.create(self.sid, dict(self))
        self.entity.put()
        store.set_secure_cookie(response, name, {'_sid': self.sid}, **kwargs)


class MemcacheSession(_BaseSession):
    @classmethod
    def _get_by_sid(cls, sid, **kwargs):
        """Returns a session given a session id."""
        data = None

        if sid and _is_valid_key(sid):
            data = memcache.get(sid)

        if not data:
            return cls((), cls._get_new_sid(), modified=True)

        return cls(data, sid)

    def save_session(self, response, store, name, **kwargs):
        if not self or not self.modified:
            return

        max_age = kwargs.get('session_max_age')
        if not max_age:
            max_age = 0

        memcache.set(self.sid, dict(self), time=max_age)
        store.set_secure_cookie(response, name, {'_sid': self.sid}, **kwargs)


def _is_valid_key(key):
    """Check if a session key has the correct format."""
    return _UUID_RE.match(key.split('.')[-1]) is not None
