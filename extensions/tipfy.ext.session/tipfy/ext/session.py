# -*- coding: utf-8 -*-
"""
    tipfy.ext.session
    ~~~~~~~~~~~~~~~~~

    This extension implements sessions using datastore, memcache or secure
    cookies. It also provides an interface to get and set flash messages
    and to set and delete secure cookies or ordinary cookies, and several
    convenient mixins for the RequestHandler.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime, timedelta
import re
from time import mktime, time

from google.appengine.api import memcache
from google.appengine.ext import db

from werkzeug import cached_property
from werkzeug.contrib.securecookie import SecureCookie
from werkzeug.contrib.sessions import ModificationTrackingDict, generate_key
from werkzeug.security import gen_salt

from tipfy import Tipfy, REQUIRED_VALUE, get_config
from tipfy.ext.db import (PickleProperty, get_protobuf_from_entity,
    get_entity_from_protobuf)

#: Default configuration values for this module. Keys are:
#:
#: - ``default_backend``: Default session backend when none is specified.
#:   Built-in options are `datastore`, `memcache` or `securecookie`.
#:   Default is `securecookie`.
#:
#: - ``secret_key``: Secret key to generate session cookies. Set this to
#:   something random and unguessable. Default is
#:   :data:`tipfy.REQUIRED_VALUE` (an exception is raised if it is not set).
#:
#: - ``cookie_name``: Name of the cookie to save a session or session id.
#:   Default is `tipfy.session`.
#:
#: - ``cookie_args``: default keyword arguments to set a cookie or
#:   securecookie. Keys are:
#:
#:   - ``cookie_session_expires``: Session expiration time in seconds. Limits
#:     the duration of the contents of a cookie, even if a session cookie
#:     exists. If ``None``, the contents lasts as long as the cookie is valid.
#:     Default is ``None``.
#:
#:   - ``cookie_max_age``: Cookie max age in seconds. Limits the duration
#:     of a session cookie. If ``None``, the cookie lasts until the client
#:     is closed. Default is ``None``.
#:
#:   - ``cookie_domain``: Domain of the cookie. To work accross subdomains the
#:     domain must be set to the main domain with a preceding dot, e.g.,
#:     cookies set for `.mydomain.org` will work in `foo.mydomain.org` and
#:     `bar.mydomain.org`. Default is ``None``, which means that cookies will
#:     only work for the current subdomain.
#:
#:   - ``cookie_path``: Path in which the authentication cookie is valid.
#:     Default is `/`.
#:
#:   - ``cookie_secure``: Make the cookie only available via HTTPS.
#:
#:   - ``cookie_httponly``: Disallow JavaScript to access the cookie.
#:
#:   - ``cookie_force``: If ``True``, force cookie to be saved on each request,
#:     even if the session data isn't changed. Default to ``False``.
default_config = {
    'default_backend':        'securecookie',
    'secret_key':             REQUIRED_VALUE,
    'cookie_name':            'tipfy.session',
    'cookie_args': {
        'session_expires': None,
        'max_age':         None,
        'domain':          None,
        'path':            '/',
        'secure':          None,
        'httponly':        False,
        'force':           False,
    }
}

# Validate session keys.
_sha1_re = re.compile(r'^[a-f0-9]{40}$')


def is_valid_key(key):
    """Check if a session key has the correct format."""
    return _sha1_re.match(key) is not None


class SessionStore(object):
    """A session store that works with multiple backends. This is responsible
    for providing and persisting sessions, flash messages, secure cookies and
    ordinary cookies.
    """
    def __init__(self, request, config, backends, default_backend):
        # The current request.
        self.request = request
        # Configuration for the sessions.
        self.config = config
        # Secure cookies to be saved at the end of request.
        self._cookies = {}
        # Tracked sessions.
        self._sessions = {}
        # A dictionary of support backend classes.
        self.backends = backends
        # The default backend to use when none is provided.
        self.default_backend = default_backend

    def get_session(self, key=None, backend=None, **kwargs):
        """Returns a session for a given key. If the session doesn't exist, a
        new session is returned.

        :param key:
            Cookie unique name. If not provided, uses the ``cookie_name``
            value configured for this module.
        :param kwargs:
            Options to save the cookie. Normally not used as the configured
            defaults are enough for most cases. Possible keywords are same as
            in ``werkzeug.contrib.securecookie.SecureCookie.save_cookie``:

            - expires
            - session_expires
            - max_age
            - path
            - domain
            - secure
            - httponly
            - force
        :return:
            A dictionary-like session object.
        """
        key = key or self.config['cookie_name']

        if key not in self._sessions:
            _kwargs = self.config['cookie_args'].copy()
            _kwargs.update(kwargs)

            backend = backend or self.default_backend
            self._sessions[key] = self.backends[backend].get_session(self,
                key, **_kwargs)

        return self._sessions[key]

    def get_flash(self, key=None, backend=None, **kwargs):
        """Returns a flash message. Flash messages are deleted when first read.

        :param key:
            Cookie unique name. If not provided, uses the ``flash_cookie_name``
            value configured for this module.
        :param kwargs:
            Options to save the cookie. Normally not used as the configured
            defaults are enough for most cases.

            See :meth:`SessionStore.get_session`.
        :return:
            The data stored in the flash, or an empty list.
        """
        session = self.get_session(key=key, backend=backend, **kwargs)
        return session.pop('_flash', [])

    def set_flash(self, data, key=None, backend=None, **kwargs):
        """Sets a flash message. Flash messages are deleted when first read.

        :param data:
            Dictionary to be saved in the flash message.
        :param key:
            Cookie unique name. If not provided, uses the ``flash_cookie_name``
            value configured for this module.
        :param kwargs:
            Options to save the cookie. Normally not used as the configured
            defaults are enough for most cases.

            See :meth:`SessionStore.get_session`.
        :return:
            ``None``.
        """
        session = self.get_session(key=key, backend=backend, **kwargs)
        session.setdefault('_flash', []).append(data)

    def get_secure_cookie(self, key, load=True, override=False, **kwargs):
        """Returns a secure cookie. Cookies get through this method are
        registered and automatically saved at the end of request.

        :param key:
            Cookie unique name.
        :param load:
            ``True`` to try to load an existing cookie from the request. If it
            is not set, a clean secure cookie is returned. ``False`` to return
            a new secure cookie. Default is ``False``.
        :param override:
            If ``True``, loads or creates a new cookie instead of reusing one
            previously set in the session store. Default to ``False``.
        :param kwargs:
            Options to save the cookie. Normally not used as the configured
            defaults are enough for most cases.

            See :meth:`SessionStore.get_session`.
        :return:
            A ``werkzeug.contrib.SecureCookie`` instance.
        """
        if override is True or key not in self._cookies:
            if load:
                cookie = self.load_secure_cookie(key)
            else:
                cookie = self.create_secure_cookie()

            self._cookies[key] = (cookie, kwargs)

        return self._cookies[key][0]

    def load_secure_cookie(self, key):
        """Loads and returns a secure cookie from request. If it is not set, a
        new secure cookie is returned.

        This cookie must be saved using a response object at the end of a
        request. To get a cookie that is saved automatically, use
        :meth:`SessionStore.get_secure_cookie`.

        :param key:
            Cookie unique name.
        :return:
            A ``werkzeug.contrib.SecureCookie`` instance.
        """
        return SecureCookie.load_cookie(self.request, key=key,
            secret_key=self.config['secret_key'])

    def create_secure_cookie(self, data=None):
        """Returns a new secure cookie.

        This cookie must be saved using a response object at the end of a
        request. To get a cookie that is saved automatically, use
        :meth:`SessionStore.get_secure_cookie`.

        :param data:
            A dictionary to be loaded into the secure cookie.
        :return:
            A ``werkzeug.contrib.SecureCookie`` instance.
        """
        if data is not None and not isinstance(data, dict):
            raise ValueError('Secure cookie data must be a dict.')

        return SecureCookie(data=data, secret_key=self.config['secret_key'])

    def set_cookie(self, key, value, **kwargs):
        """Registers a cookie or secure cookie to be saved or deleted.

        :param key:
            Cookie unique name.
        :param value:
            A cookie value or a ``werkzeug.contrib.SecureCookie`` instance.
        :param kwargs:
            Keyword arguments to save the cookie. Normally not used as the
            configured defaults are enough for most cases.

            See :meth:`SessionStore.get_session`.
        :return:
            ``None``.
        """
        self._cookies[key] = (value, kwargs)

    def delete_cookie(self, key, **kwargs):
        """Registers a cookie or secure cookie to be deleted.

        :param key:
            Cookie unique name.
        :param kwargs:
            Keyword arguments to delete the cookie. Normally not used as the
            configured defaults are enough for most cases.

            See :meth:`SessionStore.get_session`.
        :return:
            ``None``.
        """
        self._cookies[key] = (None, kwargs)

    def save_session(self, response):
        """Saves all sessions to a response object.

        :param response:
            A :class:`tipfy.Response` instance.
        :return:
            ``None``.
        """
        if not self._cookies and not self._sessions:
            return

        cookie_args = self.config['cookie_args']

        # Save all cookies.
        for key, (value, kwargs) in self._cookies.iteritems():
            kwargs = kwargs.copy() or cookie_args.copy()

            if not value:
                # Cookie is empty or marked for deletion, so delete it.
                response.delete_cookie(key, path=kwargs.get('path', '/'),
                    domain=kwargs.get('domain', None))
                # Delete session, if it exists.
                session = self._sessions.pop(key, None)
                if session:
                    session.delete_session(self, response, key, **kwargs)
            elif isinstance(value, basestring):
                # Save a normal cookie. Remove securecookie specific args.
                kwargs.pop('force', None)
                kwargs.pop('session_expires', None)
                response.set_cookie(key, value=value, **kwargs)
            elif isinstance(value, SecureCookie):
                # Save a secure cookie if modified or forced.
                kwargs = self._prepare_kwargs(kwargs)
                value.save_cookie(response, key=key, **kwargs)

        # Save all sessions.
        for key, value in self._sessions.iteritems():
            cookie_data = self._cookies.get(key)
            if cookie_data:
                kwargs = cookie_data[1].copy()
            else:
                kwargs = cookie_args.copy()

            kwargs = self._prepare_kwargs(kwargs)
            value.save_session(self, response, key, **kwargs)

    def _prepare_kwargs(self, kwargs):
        max_age = kwargs.pop('max_age', None)
        session_expires = kwargs.pop('session_expires', None)

        if max_age and 'expires' not in kwargs:
            kwargs['expires'] = time() + max_age

        if session_expires:
            kwargs['session_expires'] = datetime.fromtimestamp(time() +
                session_expires)

        return kwargs


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

        :return:
            A session unique id.
        """
        return self.key().name()

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
            session = SessionModel.get_by_key_name(sid)
            if session:
                session.set_cache()

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
            namespace=self.__class__.get_namespace())

    def delete_cache(self):
        """Saves a new cache for this entity."""
        memcache.delete(self.sid, namespace=self.__class__.get_namespace())

    def put(self):
        """Saves the session and updates the memcache entry."""
        self.set_cache()
        db.put(self)

    def delete(self):
        """Deletes the session and the memcache entry."""
        self.delete_cache()
        db.delete(self)


class BaseSession(ModificationTrackingDict):
    """A container for session data. This is a dictionary that tracks
    changes.
    """
    __slots__ = ModificationTrackingDict.__slots__ + ('sid', 'new')

    def __init__(self, data, sid, new=False):
        ModificationTrackingDict.__init__(self, data)
        self.sid = sid
        self.new = new

    @classmethod
    def get_session(cls, store, key, **kwargs):
        """Returns a session that is tracked by the session store."""
        cookie = store.get_secure_cookie(key, **kwargs)
        sid = cookie.get('_sid', None)
        session = cls.get_by_sid(sid)

        if sid != session.sid:
            cookie['_sid'] = session.sid

        return session


class DatastoreSession(BaseSession):
    """A session container for datastore sessions."""
    __slots__ = BaseSession.__slots__ + ('entity',)

    model_class = SessionModel

    def __init__(self, data, sid, new=False, entity=None):
        BaseSession.__init__(self, data, sid, new=new)
        self.entity = entity

    @classmethod
    def get_by_sid(cls, sid):
        """Returns a session given a session id."""
        entity = None

        if sid and is_valid_key(sid):
            entity = cls.model_class.get_by_sid(sid)

        if not entity:
            return cls({}, generate_key(gen_salt(10)), new=True)

        return cls(entity.data, sid, new=False, entity=entity)

    @classmethod
    def delete_by_sid(cls, sid):
        entity = cls.model_class.get_by_sid(sid)
        if entity:
            entity.delete()

    @classmethod
    def get_session(cls, store, key, **kwargs):
        """Returns a session that is tracked by the session store."""
        cookie = store.get_secure_cookie(key, **kwargs)
        sid = cookie.get('_sid', None)
        session = cls.get_by_sid(sid)

        if sid != session.sid:
            cookie['_sid'] = session.sid

        if session.entity:
            seconds = kwargs.get('session_expires')
            if seconds and (session.entity.created + \
                timedelta(seconds=seconds) < datetime.utcnow()):
                # Entity is too old.
                session.clear()
                session.entity = None

        return session

    def save_session(self, store, response, key, **kwargs):
        """Saves a session."""
        if not self.modified:
            return

        self.entity = self.model_class.create(self.sid, dict(self))
        self.entity.put()

    def delete_session(self, store, response, key, **kwargs):
        """Deletes a session."""
        if self.entity and self.entity.is_saved():
            self.entity.delete()


class MemcacheSession(BaseSession):
    """A session container for memcache sessions."""
    @classmethod
    def get_namespace(cls):
        return cls.__module__ + '.' + cls.__name__

    @classmethod
    def get_by_sid(cls, sid):
        """Returns a session given a session id."""
        data = None

        if sid and is_valid_key(sid):
            data = memcache.get(sid, namespace=cls.get_namespace())

        if not data:
            return cls({}, generate_key(gen_salt(10)), new=True)

        return cls(data, sid, new=False)

    @classmethod
    def delete_by_sid(cls, sid):
        memcache.delete(sid, namespace=cls.get_namespace())

    def save_session(self, store, response, key, **kwargs):
        """Saves a session."""
        if not self.modified:
            return

        expires = kwargs.get('session_expires', kwargs.get('expires', 0))
        if isinstance(expires, datetime):
            expires = mktime(expires.timetuple())

        memcache.set(self.sid, dict(self), time=expires,
            namespace=self.__class__.get_namespace())

    def delete_session(self, store, response, key, **kwargs):
        """Deletes a session."""
        if self.sid:
            self.__class__.delete_by_sid(self.sid)


class SecureCookieSession(SecureCookie):
    """A session container for SecureCookie sessions."""
    @classmethod
    def get_session(cls, store, key, **kwargs):
        return cls.load_cookie(store.request, key=key,
            secret_key=store.config['secret_key'])

    def save_session(self, store, response, key, **kwargs):
        """Saves a session."""
        self.save_cookie(response, key=key, **kwargs)

    def delete_session(self, store, response, key, **kwargs):
        """Deletes a session."""
        response.delete_cookie(key, path=kwargs.get('path', '/'),
                    domain=kwargs.get('domain', None))


class SessionMiddleware(object):
    #: A dictionary with the default supported backends.
    default_backends = {
        'datastore':    DatastoreSession,
        'memcache':     MemcacheSession,
        'securecookie': SecureCookieSession,
    }

    def __init__(self, backends=None, default_backend=None):
        self.backends = backends or self.default_backends
        self.default_backend = default_backend or get_config(__name__,
            'default_backend')

    def pre_dispatch(self, handler):
        handler.request.registry['session_store'] = SessionStore(
            handler.request, get_config(__name__), self.backends,
            self.default_backend)

    def post_dispatch(self, handler, response):
        handler.request.registry['session_store'].save_session(response)
        return response

    def pre_dispatch_handler(self):
        request = Tipfy.request
        request.registry['session_store'] = SessionStore(request,
            get_config(__name__), self.backends, self.default_backend)

    def post_dispatch_handler(self, response):
        Tipfy.request.registry['session_store'].save_session(response)
        return response


class BaseSessionMixin(object):
    """Base class for all session-related mixins."""
    @cached_property
    def session_store(self):
        return self.request.registry['session_store']


class CookieMixin(BaseSessionMixin):
    """A mixin that adds set_cookie() and delete_cookie() methods to a
    :class:`tipfy.RequestHandler`. Must be used with :class:`SessionMiddleware`.
    """
    def set_cookie(self, key, value, **kwargs):
        self.session_store.set_cookie(key, value, **kwargs)

    def delete_cookie(self, key, **kwargs):
        self.session_store.delete_cookie(key, **kwargs)


class SecureCookieMixin(BaseSessionMixin):
    """A mixin that adds a get_secure_cookie() method to a
    :class:`tipfy.RequestHandler`. Must be used with :class:`SessionMiddleware`.
    """
    def get_secure_cookie(self, key, load=True, override=False, **kwargs):
        """Returns a tracked secure cookie. See
        :meth:`SessionStore.get_secure_cookie`.
        """
        return self.session_store.get_secure_cookie(key, load, override,
            **kwargs)


class FlashMixin(BaseSessionMixin):
    """A mixin that adds get_flash() and set_flash() methods to a
    :class:`tipfy.RequestHandler`. Must be used with :class:`SessionMiddleware`.
    """
    def get_flash(self, key=None, backend=None, **kwargs):
        """Returns a flash message. See :meth:`SessionStore.get_flash`."""
        return self.session_store.get_flash(key, backend, **kwargs)

    def set_flash(self, data, key=None, backend=None, **kwargs):
        """Sets a flash message. See :meth:`SessionStore.set_flash`."""
        self.session_store.set_flash(data, key, backend, **kwargs)


class MessagesMixin(BaseSessionMixin):
    """A :class:`tipfy.RequestHandler` mixin for system messages."""
    @cached_property
    def messages(self):
        """A list of status messages to be displayed to the user."""
        if getattr(self, '_MessagesMixin__messages', None) is None:
            # Initialize messages list and check for flashes on first access.
            self.__messages = []
            self.__messages.extend(self.session_store.get_flash())

        return self.__messages

    def set_message(self, level, body, title=None, life=5, flash=False):
        """Adds a status message.

        :param level:
            Message level. Common values are "success", "error", "info" or
            "alert".
        :param body:
            Message contents.
        :param title:
            Optional message title.
        :param life:
            Message life time in seconds. User interface can implement
            a mechanism to make the message disappear after the elapsed time.
            If not set, the message is permanent.
        :return:
            ``None``.
        """
        message = {'level': level, 'title': title, 'body': body, 'life': life}
        if flash is True:
            self.session_store.set_flash(message)
        else:
            self.messages.append(message)


class SessionMixin(BaseSessionMixin):
    """A :class:`tipfy.RequestHandler` that provides access to the current
    session.
    """
    @cached_property
    def session(self):
        """A dictionary-like object that is persisted at the end of the
        request.
        """
        return self.session_store.get_session()

    def get_session(self, key=None, backend=None, **kwargs):
        """Returns a session. See :meth:`SessionStore.get_session`."""
        return self.session_store.get_session(key, backend, **kwargs)


class AllSessionMixins(CookieMixin, SecureCookieMixin, FlashMixin,
    MessagesMixin, SessionMixin):
    """All session mixins combined in one."""
