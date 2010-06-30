# -*- coding: utf-8 -*-
"""
    tipfy.ext.session
    ~~~~~~~~~~~~~~~~~

    This extension provides sessions using datastore, memcache or secure
    cookies. It also provides an interface to get and set flash messages,
    and to set and delete secure cookies or ordinary cookies, and several
    convenient mixins for the RequestHandler.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime, timedelta
import re
from time import time

from google.appengine.api import memcache
from google.appengine.ext import db

from werkzeug import cached_property
from werkzeug.contrib.securecookie import SecureCookie
from werkzeug.contrib.sessions import Session as BaseSession, generate_key
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
#: - ``cookie_name``: Name of the cookie to save a session. Default
#:   is `tipfy.session`.
#:
#: - ``cookie_session_expires``: Session expiration time in seconds. Limits the
#:   duration of the contents of a cookie, even if a session cookie exists.
#:   If ``None``, the contents lasts as long as the cookie is valid. Default is
#:   ``None``.
#:
#: - ``cookie_max_age``: Cookie max age in seconds. Limits the duration of a
#:   session cookie. If ``None``, the cookie lasts until the client is closed.
#:   Default is ``None``.
#:
#: - ``cookie_domain``: Domain of the cookie. To work accross subdomains the
#:   domain must be set to the main domain with a preceding dot, e.g., cookies
#:   set for `.mydomain.org` will work in `foo.mydomain.org` and
#:   `bar.mydomain.org`. Default is ``None``, which means that cookies will
#:   only work for the current subdomain.
#:
#: - ``cookie_path``: Path in which the authentication cookie is valid.
#:   Default is `/`.
#:
#: - ``cookie_secure``: Make the cookie only available via HTTPS.
#:
#: - ``cookie_httponly``: Disallow JavaScript to access the cookie.
#:
#: - ``cookie_force``: If ``True``, force cookie to be saved on each request,
#:   even if the session data isn't changed. Default to ``False``.
default_config = {
    'default_backend':        'securecookie',
    'secret_key':             REQUIRED_VALUE,
    'cookie_name':            'tipfy.session',
    'cookie_session_expires': None,
    'cookie_max_age':         None,
    'cookie_domain':          None,
    'cookie_path':            '/',
    'cookie_secure':          None,
    'cookie_httponly':        False,
    'cookie_force':           False,
}

# Validate session keys.
_sha1_re = re.compile(r'^[a-f0-9]{40}$')


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
        # Session and cookie data to be saved at the end of request.
        self._data = {}
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

        if key not in self._data or self._data[key][0] is None:
            backend = backend or self.default_backend
            session = self.backends[backend].get_session(self, key, **kwargs)
            self._data[key] = (session, kwargs)

        return self._data[key][0]

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
        if override is True or key not in self._data:
            if load:
                cookie = self.load_secure_cookie(key)
            else:
                cookie = self.create_secure_cookie()

            self._data[key] = (cookie, kwargs)

        return self._data[key][0]

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
        self._data[key] = (value, kwargs)

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
        self._data[key] = (None, kwargs)

    def save_session(self, response):
        """Saves all sessions to a response object.

        :param response:
            A :class:`tipfy.Response` instance.
        :return:
            ``None``.
        """
        if not self._data:
            return

        for key, (value, kwargs) in self._data.iteritems():
            kwargs = kwargs or self.cookie_args.copy()

            if not value:
                # Session is empty, so delete it.
                response.delete_cookie(key, path=kwargs.get('path', '/'),
                    domain=kwargs.get('domain', None))
                if hasattr(value, 'delete_session'):
                    value.delete_session()
            elif isinstance(value, basestring):
                # Save a normal cookie. Remove securecookie specific args.
                kwargs.pop('force', None)
                kwargs.pop('session_expires', None)
                response.set_cookie(key, value=value, **kwargs)
            elif hasattr(value, 'save_cookie'):
                # Save a session cookie, if modified or forced.
                max_age = kwargs.pop('max_age', None)
                session_expires = kwargs.pop('session_expires', None)

                if max_age and 'expires' not in kwargs:
                    kwargs['expires'] = time() + max_age

                if session_expires:
                    kwargs['session_expires'] = datetime.fromtimestamp(
                        time() + session_expires)

                value.save_cookie(response, key=key, **kwargs)

        # Remove all values.
        self._data.clear()


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

    @property
    def valid(self):
        """Returns ``True`` if the session has not expired.

        :return:
            ``True`` if the session has not expired, ``False`` otherwise.
        """
        seconds = get_config(__name__, 'cookie_session_expires')
        if not seconds:
            return True

        return self.created + timedelta(seconds=seconds) < datetime.now()

    @property
    def namespace(self):
        """Returns the namespace to be used in memcache.

        :return:
            A namespace string.
        """
        return SessionModel.get_namespace()

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


class Session(BaseSession):
    __slots__ = BaseSession.__slots__ + ('backend',)

    def __init__(self, data, sid, backend, new=False):
        BaseSession.__init__(self, data, sid, new)
        self.backend = backend

    def save_cookie(self, response, **kwargs):
        self.backend.save_if_modified(self, **kwargs)

    def delete_session(self):
        self.backend.delete(self)


class DatastoreSession(Session):
    """A session dictionary that stores a reference to the session entity.
    """
    __slots__ = Session.__slots__ + ('entity',)

    def __init__(self, data, sid, backend, new=False, entity=None):
        Session.__init__(self, data, sid, backend, new)
        self.entity = entity


class BaseSessionBackend(object):
    session_class = Session

    def is_valid_key(self, key):
        """Check if a session key has the correct format."""
        return _sha1_re.match(key) is not None

    def generate_key(self, salt=None):
        """Returns a new session key."""
        return generate_key(salt or gen_salt(10))

    def new(self):
        """Generates a new session."""
        return self.session_class({}, self.generate_key(), self, True)

    def save_if_modified(self, session, **kwargs):
        """Save if a session class wants an update."""
        if session.should_save:
            self.save(session, **kwargs)

    def get(self, sid=None):
        """Returns a session given a session id."""

    def save(self, session, **kwargs):
        """Saves a session."""

    def delete(self, session):
        """Deletes a session."""

    def get_session(self, store, key, **kwargs):
        """Returns a session that is tracked by the session store."""
        cookie = store.get_secure_cookie(key, **kwargs)
        sid = cookie.get('_sid', None)
        session = self.get(sid=sid)

        if sid != session.sid:
            cookie['_sid'] = session.sid

        return session


class DatastoreSessionBackend(BaseSessionBackend):
    model_class = SessionModel
    session_class = DatastoreSession

    def get(self, sid=None):
        """Returns a session given a session id."""
        if not sid or not self.is_valid_key(sid):
            return self.new()

        entity = self.model_class.get_by_sid(sid)
        if not entity:
            return self.new()

        return self.session_class(entity.data, sid, self, False, entity)

    def save(self, session, **kwargs):
        """Saves a session."""
        session.entity = self.model_class.create(session.sid, dict(session))
        session.entity.put()

    def delete(self, session):
        """Deletes a session."""
        if session.entity and session.entity.is_saved():
            session.entity.delete()


class MemcacheSessionBackend(BaseSessionBackend):
    @cached_property
    def namespace(self):
        """Returns the namespace to be used in memcache.

        :return:
            A namespace string.
        """
        return self.__class__.__module__ + '.' + self.__class__.__name__

    def get(self, sid=None):
        """Returns a session given a session id."""
        if not sid or not self.is_valid_key(sid):
            return self.new()

        data = memcache.get(sid, namespace=self.namespace)
        if not data:
            return self.new()

        return self.session_class(data, sid, False)

    def save(self, session, **kwargs):
        """Saves a session."""
        # TODO set expiration from kwargs.
        memcache.set(session.sid, dict(session), namespace=self.namespace)

    def delete(self, session):
        """Deletes a session."""
        memcache.delete(session.sid, namespace=self.namespace)


class SecureCookieSessionBackend(object):
    def get_session(self, store, key, **kwargs):
        """Returns a session that is tracked by the session store."""
        return store.get_secure_cookie(key, **kwargs)


class SessionMiddleware(object):
    #: A dictionary with the default supported backends.
    default_backends = {
        'datastore':    DatastoreSessionBackend(),
        'memcache':     MemcacheSessionBackend(),
        'securecookie': SecureCookieSessionBackend(),
    }

    def __init__(self, backends=None, default_backend=None):
        self.backends = backends or self.default_backends
        self.default_backend = default_backend or get_config(__name__,
            'default_backend')

    def pre_dispatch(self, handler):
        handler.request.registry['session_store'] = SessionStore(
            handler.request, self.config, self.backends, self.default_backend)

    def post_dispatch(self, handler, response):
        handler.request.registry['session_store'].save_session(response)

    @cached_property
    def config(self):
        config = get_config(__name__).copy()
        config['cookie_args'] = {
            'session_expires': config.pop('cookie_session_expires'),
            'max_age':         config.pop('cookie_max_age'),
            'domain':          config.pop('cookie_domain'),
            'path':            config.pop('cookie_path'),
            'secure':          config.pop('cookie_secure'),
            'httponly':        config.pop('cookie_httponly'),
            'force':           config.pop('cookie_force'),
        }
        return config


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
        :life:
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
