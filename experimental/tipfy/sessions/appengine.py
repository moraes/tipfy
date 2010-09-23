import re
import uuid

from google.appengine.api import memcache
from google.appengine.ext import db

from werkzeug.contrib.sessions import ModificationTrackingDict

# Validate session keys.
_UUID_RE = re.compile(r'^[a-f0-9]{32}$')


def is_valid_key(key):
    """Check if a session key has the correct format."""
    return _UUID_RE.match(key.split('.')[-1]) is not None


class DatastoreSession(ModificationTrackingDict):
    @classmethod
    def get_session(cls, store, name, **kwargs):
        """TODO"""
        raise NotImplementedError()

    def save_session(self, response, store, name, **kwargs):
        """TODO"""
        raise NotImplementedError()


class MemcacheSession(ModificationTrackingDict):
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
    def _get_by_sid(cls, sid):
        """Returns a session given a session id."""
        data = None

        if sid and is_valid_key(sid):
            data = memcache.get(sid)

        if not data:
            return cls((), cls._get_new_sid(), modified=True)

        return cls(data, sid)

    @classmethod
    def get_session(cls, store, name, **kwargs):
        cookie = store.get_secure_cookie(name) or {}
        return cls._get_by_sid(cookie.get('_sid'))

    def save_session(self, response, store, name, **kwargs):
        if not self.modified:
            return

        max_age = kwargs.get('session_max_age')
        if not max_age:
            max_age = 0

        memcache.set(self.sid, dict(self), time=max_age)
        store.set_secure_cookie(response, name, {'_sid': self.sid}, **kwargs)
