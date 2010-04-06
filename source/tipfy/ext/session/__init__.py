# -*- coding: utf-8 -*-
"""
    tipfy.ext.session
    ~~~~~~~~~~~~~~~~~

    Session extension.

    This module provides sessions using secure cookies or the datastore.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime
from time import time

from google.appengine.api import memcache
from google.appengine.ext import db

from werkzeug.contrib.securecookie import SecureCookie
from werkzeug.contrib.sessions import generate_key, ModificationTrackingDict

from tipfy import cached_property, local, get_config, REQUIRED_CONFIG
from tipfy.ext.db import (get_protobuf_from_entity, get_entity_from_protobuf,
    PickleProperty)
from tipfy.ext.i18n import _

#: Default configuration values for this module. Keys are:
#:
#: - ``session_type``: Session storage type. Available options are
#:   `securecookie` or `datastore`. Default is `securecookie`.
#:
#: - ``secret_key``: Secret key to generate session cookies. Set this to
#:   something random and unguessable. Default is
#:   :data:`tipfy.REQUIRED_CONFIG` (an exception is raised if it is not set).
#:
#: - ``session_cookie_name``: Name of the cookie to save a session. Default
#:   is `tipfy.session`.
#:
#: - ``flash_cookie_name``: Name of the cookie to save a flash message.
#:   Default is `tipfy.flash`.
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
    'session_type':        'securecookie',
    'secret_key':          REQUIRED_CONFIG,
    'session_cookie_name': 'tipfy.session',
    'flash_cookie_name':   'tipfy.flash',
    'cookie_session_expires': None,
    'cookie_max_age':  None,
    'cookie_domain':   None,
    'cookie_path':     '/',
    'cookie_secure':   None,
    'cookie_httponly': False,
    'cookie_force':    False,
}


class SessionMiddleware(object):
    """A middleware that initializes and persists sessions for a
    :class:`tipfy.RequestHandler`.
    """
    def pre_dispatch(self, handler):
        """Executes before a :class:`tipfy.RequestHandler` is dispatched. If
        it returns a response object, it will stop the pre_dispatch middleware
        chain and won't run the requested handler method, using the returned
        response instead. However, post_dispatch hooks will still be executed.

        :param handler:
            A :class:`tipfy.RequestHandler` instance.
        :return:
            A ``werkzeug.Response`` instance or ``None``.
        """
        if self.session_type == 'securecookie':
            local.session_store = SessionStore(self)
        elif self.session_type == 'datastore':
            local.session_store = DatastoreSessionStore(self)

    def post_dispatch(self, handler, response):
        """Executes after a :class:`tipfy.RequestHandler` is dispatched. It
        must always return a response object, be it the one passed in the
        arguments or a new one.

        :param handler:
            A :class:`tipfy.RequestHandler` instance.
        :param response:
            A ``werkzeug.Response`` instance.
        :return:
            A ``werkzeug.Response`` instance.
        """
        if getattr(local, 'session_store', None) is not None:
            local.session_store.save(response)

        return response

    def pre_dispatch_handler(self):
        """Called if session is used as a WSGIApplication middleware."""
        self.pre_dispatch(None)
        return None

    def post_dispatch_handler(self, response):
        """Called if session is used as a WSGIApplication middleware."""
        return self.post_dispatch(None, response)

    @cached_property
    def session_type(self):
        return get_config(__name__, 'session_type')

    @cached_property
    def secret_key(self):
        return get_config(__name__, 'secret_key')

    @cached_property
    def default_session_key(self):
        return get_config(__name__, 'session_cookie_name')

    @cached_property
    def default_flash_key(self):
        return get_config(__name__, 'flash_cookie_name')

    @cached_property
    def default_cookie_args(self):
        """Default keyword arguments to set or delete a cookie or securecookie.
        """
        config = get_config(__name__)
        return {
            'session_expires': config.get('cookie_session_expires'),
            'max_age':         config.get('cookie_max_age'),
            'domain':          config.get('cookie_domain'),
            'path':            config.get('cookie_path'),
            'secure':          config.get('cookie_secure'),
            'httponly':        config.get('cookie_httponly'),
            'force':           config.get('cookie_force'),
        }


class SessionMixin(object):
    """A :class:`tipfy.RequestHandler` mixin that provides access to session
    and functions to get and set flash messages.
    """
    @cached_property
    def session(self):
        """A dictionary-like object that is persisted at the end of the request.
        """
        return local.session_store.get_session()

    def get_flash(self, key=None):
        """Returns a flash message. Flash messages are stored in a signed
        cookie and deleted when read.

        :param key:
            Cookie unique name. If not provided, uses the ``flash_cookie_name``
            value configured for this module.
        :return:
            The data stored in the flash, or ``None``.
        """
        return local.session_store.get_flash(key)

    def set_flash(self, data, key=None):
        """Sets a flash message. Flash messages are stored in a signed cookie
        and deleted when read.

        :param data:
            Dictionary to be saved in the flash message.
        :param key:
            Cookie unique name. If not provided, uses the ``flash_cookie_name``
            value configured for this module.
        :return:
            ``None``.
        """
        return local.session_store.set_flash(data, key)


class MessagesMixin(SessionMixin):
    """A :class:`tipfy.RequestHandler` mixin for system messages."""
    @cached_property
    def messages(self):
        """A list of status messages to be displayed to the user."""
        if getattr(self, '_MessagesMixin__messages', None) is None:
            # Initialize messages list and check for flashes on first access.
            self.__messages = []
            flash = self.get_flash()
            if flash:
                self.__messages.append(flash)

        return self.__messages

    def set_message(self, level, body, title=None, life=5000, flash=False):
        """Adds a status message.

        :param level:
            Message level. Common values are "success", "error", "info" or
            "alert".
        :param body:
            Message contents.
        :param title:
            Optional message title.
        :life:
            Message life time in milliseconds. User interface can implement
            a mechanism to make the message disappear after the elapsed time.
            If not set, the message is permanent.
        :return:
            ``None``.
        """
        message = {'level': level, 'title': title, 'body': body, 'life': life}
        if flash is True:
            self.set_flash(message)
        else:
            self.messages.append(message)

    def set_form_error(self, body=None, title=None):
        """Adds a form error message.

        :param body:
            Message contents.
        :param title:
            Optional message title.
        :return:
            ``None``.
        """
        if body is None:
            body = _('A problem occurred. Please correct the errors listed in '
                'the form.')

        if title is None:
            title = _('Error')

        self.set_message('error', body, title=title, life=None)


class SessionStore(object):
    """A session store that uses secure cookies for storage. Additionally
    provides signed flash messages and secure cookies that persist
    automatically.
    """
    def __init__(self, config):
        """Initializes the store with empty contents.

        :param config:
            Configuration provider.
        """
        self.config = config
        # Cookies to save or delete.
        self._data = {}
        # Arguments for each secure cookie. If not set, use default values.
        self._data_args = {}
        # Flash messages marked as read.
        self._flash_read = []

    def save(self, response):
        """Saves all cookies tracked by this store.

        :param response:
            A ``werkzeug.Response`` instance.
        :return:
            ``None``.
        """
        if not self._data:
            return

        cookie_args = self.config.default_cookie_args

        for key, cookie in self._data.iteritems():
            # Use special cookie arguments, if set.
            kwargs = self._data_args.get(key, None) or dict(cookie_args)

            if not cookie:
                # Cookie is None (marked for deletion) or empty. So delete it.
                path = kwargs.get('path', '/')
                domain = kwargs.get('domain', None)
                response.delete_cookie(key, path=path, domain=domain)
            elif isinstance(cookie, basestring):
                # Save a normal cookie. Remove securecookie specific args.
                kwargs.pop('force', None)
                kwargs.pop('session_expires', None)
                response.set_cookie(key, value=cookie, **kwargs)
            else:
                # Save a secure cookie, if modified or forced.
                max_age = kwargs.pop('max_age', None)
                session_expires = kwargs.pop('session_expires', None)

                if max_age and 'expires' not in kwargs:
                    kwargs['expires'] = time() + max_age

                if session_expires:
                    kwargs['session_expires'] = datetime.fromtimestamp(
                        time() + session_expires)

                cookie.save_cookie(response, key=key, **kwargs)

    def get_session(self, key=None, **kwargs):
        """Returns a session for a given key. If the session doesn't exist, a
        new session is returned.

        :param key:
            Cookie unique name. If not provided, uses the
            ``session_cookie_name`` value configured for this module.
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
        key = key or self.config.default_session_key

        if key not in self._data:
            # Load a session from request.
            self._data[key] = self._load_session(key)
            self._data_args[key] = kwargs
        elif self._data[key] is None:
            # Session was previously deleted. Create a new one.
            self._data[key] = self._create_session()
            self._data_args[key] = kwargs

        return self._data[key]

    def _load_session(self, key):
        """Returns a session for a given key. This is the session factory
        method.

        :param key:
            Cookie unique name. If not provided, uses the
            ``session_cookie_name`` value configured for this module.
        :return:
            A dictionary-like session object.
        """
        return self.load_secure_cookie(key)

    def _create_session(self):
        """Returns a new session. This is the session factory method.

        :return:
            A dictionary-like session object.
        """
        return self.create_secure_cookie()

    def delete_session(self, key=None, **kwargs):
        """Deletes a session for a given key.

        :param key:
            Cookie unique name. If not provided, uses the
            ``session_cookie_name`` value configured for this module.
        :param kwargs:
            Options to save the cookie. Normally not used as the configured
            defaults are enough for most cases.

            See :meth:`SessionStore.get_session`.
        :return:
            ``None``.
        """
        key = key or self.config.default_session_key

        if self._data.get(key, None) is not None:
            self._delete_session(self._data[key])

        self._data[key] = None
        self._data_args[key] = kwargs

    def _delete_session(self, session):
        """Deletes a session for a given key.

        :param key:
            Cookie unique name. If not provided, uses the
            ``session_cookie_name`` value configured for this module.
        :return:
            ``None``.
        """
        session.clear()

    def get_secure_cookie(self, key, load=True, override=False, **kwargs):
        """Returns a secure cookie. Cookies get through this method are tracked
        and automatically saved at the end of request if they change.

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
                self._data[key] = self.load_secure_cookie(key)
            else:
                self._data[key] = self.create_secure_cookie()

            self._data_args[key] = kwargs

        return self._data[key]

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
        return SecureCookie.load_cookie(local.request, key=key,
                                        secret_key=self.config.secret_key)

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
        return SecureCookie(data=data, secret_key=self.config.secret_key)

    def get_flash(self, key=None, **kwargs):
        """Returns a flash message. Flash messages are stored in a signed
        cookie and deleted when read.

        :param key:
            Cookie unique name. If not provided, uses the ``flash_cookie_name``
            value configured for this module.
        :param kwargs:
            Options to save the cookie. Normally not used as the configured
            defaults are enough for most cases.

            See :meth:`SessionStore.get_session`.
        :return:
            The data stored in the flash, or ``None``.
        """
        key = key or self.config.default_flash_key

        if key in self._flash_read:
            return

        self._flash_read.append(key)

        if key in local.request.cookies:
            if key not in self._data:
                # Only mark for deletion if it was not set.
                self._data[key] = None
                self._data_args[key] = kwargs

            flash = self.load_secure_cookie(key)
            if not flash:
                return None

            return flash

    def set_flash(self, data, key=None, **kwargs):
        """Sets a flash message. Flash messages are stored in a signed cookie
        and deleted when read.

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
        key = key or self.config.default_flash_key
        cookie = self.create_secure_cookie(data)
        cookie.modified = True
        self._data[key] = cookie
        self._data_args[key] = kwargs

    def set_cookie(self, key, cookie, **kwargs):
        """Sets a cookie or secure cookie to be saved or deleted at the end of
        the request.

        :param key:
            Cookie unique name.
        :param cookie:
            A cookie value or a ``werkzeug.contrib.SecureCookie`` instance.
        :param kwargs:
            Options to save the cookie. Normally not used as the configured
            defaults are enough for most cases.

            See :meth:`SessionStore.get_session`.
        :return:
            ``None``.
        """
        self._data[key] = cookie
        self._data_args[key] = kwargs


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
        data = memcache.get(sid, namespace=cls.get_namespace())
        if data:
            session = get_entity_from_protobuf(data)
        else:
            session = Session.get_by_key_name(sid)
            if session:
                session.update_cache()

        return session

    @classmethod
    def create(cls, sid):
        """Returns a new, empty session entity.

        :param sid:
            A session id.
        :return:
            A new and not saved session entity.
        """
        return cls(key_name=sid, data={})

    def put(self):
        """Saves the session and updates the memcache entry."""
        self.update_cache()
        db.Model.put(self)

    def delete(self):
        """Deletes the session and the memcache entry."""
        memcache.delete(self.sid, namespace=Session.get_namespace())
        db.Model.delete(self)

    def update_cache(self):
        """Saves a new cache for this entity."""
        data = get_protobuf_from_entity(self)
        memcache.set(self.sid, data, namespace=Session.get_namespace())


class DatastoreSession(ModificationTrackingDict):
    """A dictionary-like object with values loaded from datastore."""
    def __init__(self, cookie):
        self.cookie = cookie
        self.entity = Session.get_by_sid(cookie['sid']) or \
            Session.create(cookie['sid'])
        ModificationTrackingDict.__init__(self, self.entity.data)

    def delete(self):
        """Deletes the session from datastore."""
        if self.entity and self.entity.is_saved():
            self.entity.delete()

        self.entity = None
        # Invalidate the session id.
        del self.cookie['sid']

    def save_cookie(self, response, key, **kwargs):
        """Saves the session to datastore, if modified, and saves the cookie
        with the session id.
        """
        force = kwargs.pop('force', False)
        if self.modified:
            self.entity.data = dict(self)
            self.entity.put()
            force = True

        self.cookie.save_cookie(response, key=key, force=force, **kwargs)


class DatastoreSessionStore(SessionStore):
    """A session store that uses the datastore for storage. Additionally
    provides signed flash messages and secure cookies that persist
    automatically.
    """
    def create_session_id(self):
        """Returns a random session id.

        :return:
            A new session id.
        """
        return generate_key(self.config.secret_key)

    def _load_session(self, key):
        """Returns a session for a given key. This is the session factory
        method.

        :param key:
            Cookie unique name. If not provided, uses the
            ``session_cookie_name`` value configured for this module.
        :return:
            A dictionary-like session object.
        """
        cookie = self.load_secure_cookie(key)
        if 'sid' not in cookie:
            cookie['sid'] = self.create_session_id()

        return DatastoreSession(cookie)

    def _create_session(self):
        """Returns a new session. This is the session factory method.

        :return:
            A dictionary-like session object.
        """
        cookie = self.create_secure_cookie({'sid': self.create_session_id()})
        return DatastoreSession(cookie)

    def _delete_session(self, session):
        """Deletes a session for a given key.

        :param key:
            Cookie unique name. If not provided, uses the
            ``session_cookie_name`` value configured for this module.
        :return:
            ``None``.
        """
        session.clear()
        if isinstance(session, DatastoreSession):
            session.delete()
