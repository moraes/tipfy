# -*- coding: utf-8 -*-
"""
    tipfy.ext.session
    ~~~~~~~~~~~~~~~~~

    Session extension.

    This module provides sessions using secure cookies or the datastore.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime, timedelta

from google.appengine.api import memcache
from google.appengine.ext import db

from werkzeug.contrib.securecookie import SecureCookie
from werkzeug.contrib.sessions import generate_key, ModificationTrackingDict

from tipfy import cached_property, local, get_config, REQUIRED_CONFIG
from tipfy.ext.db import (get_entity_from_protobuf, get_protobuf_from_entity,
    retry_on_timeout, PickleProperty)

#: Default configuration values for this module. Keys are:
#:
#: - ``session_type``: Session storage type. Options are `securecookie` or
#:   `datastore`. Default is `securecookie`.
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
default_config = {
    'session_type':        'securecookie',
    'secret_key':          REQUIRED_CONFIG,
    'session_cookie_name': 'tipfy.session',
    'flash_cookie_name':   'tipfy.flash',
    'cookie_max_age': None,
    'cookie_domain': None,
    'cookie_path': '/',
    'cookie_secure': None,
    'cookie_httponly': False,
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
        return {
            'max_age':  get_config(__name__, 'cookie_max_age'),
            'domain':   get_config(__name__, 'cookie_domain'),
            'path':     get_config(__name__, 'cookie_path'),
            'secure':   get_config(__name__, 'cookie_secure'),
            'httponly': get_config(__name__, 'cookie_httponly'),
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
    def __init__(self, provider):
        """Initializes the store with empty contents.

        :param provider:
            Configuration provider.
        """
        self.provider = provider
        self._data = {}

    def save(self, response):
        """Saves all cookies tracked by this store.

        :param response:
            A ``werkzeug.Response`` instance.
        :return:
            ``None``.
        """
        if not self._data:
            return

        kwargs = self.provider.default_cookie_args

        for key, value in self._data.iteritems():
            # Cookie was set.
            #cookie, cookie_args = self._data[key]
            #cookie_args = cookie_args or kwargs
            cookie = value

            if cookie is None:
                # Cookie was marked for deletion.
                path = kwargs.get('path', '/')
                domain = kwargs.get('domain', None)
                response.delete_cookie(key, path=path, domain=domain)
            else:
                # Cookie will only be saved if it was changed.
                cookie.save_cookie(response, key=key, **kwargs)

    def get_session(self, key=None):
        """Returns a session for a given key. If the session doesn't exist, a
        new session is returned.

        :param key:
            Cookie unique name. If not provided, uses the
            ``session_cookie_name`` value configured for this module.
        :return:
            A dictionary-like session object.
        """
        key = key or self.provider.default_session_key

        if key not in self._data:
            self._data[key] = self._get_session(key)

        return self._data[key]

    def _get_session(self, key):
        """Returns a session for a given key. This is the session factory
        method.

        :param key:
            Cookie unique name. If not provided, uses the
            ``session_cookie_name`` value configured for this module.
        :return:
            A dictionary-like session object.
        """
        return self.load_secure_cookie(key)

    def delete_session(self, key=None):
        """Deletes a session for a given key.

        :param key:
            Cookie unique name. If not provided, uses the
            ``session_cookie_name`` value configured for this module.
        :return:
            ``None``.
        """
        key = key or self.provider.default_session_key

        if self._data.get(key, None) is not None:
            self._delete_session(self._data[key])

        self._data[key] = None

    def _delete_session(self, session):
        """Deletes a session for a given key.

        :param key:
            Cookie unique name. If not provided, uses the
            ``session_cookie_name`` value configured for this module.
        :return:
            ``None``.
        """
        session.clear()

    def get_flash(self, key=None):
        """Returns a flash message. Flash messages are stored in a signed
        cookie and deleted when read.

        :param key:
            Cookie unique name. If not provided, uses the ``flash_cookie_name``
            value configured for this module.
        :return:
            The data stored in the flash, or ``None``.
        """
        key = key or self.provider.default_flash_key

        if key in local.request.cookies:
            if key not in self._data:
                # Only mark for deletion if it was not set.
                self._data[key] = None

            return self.load_secure_cookie(key)

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
        key = key or self.provider.default_flash_key
        self._data[key] = self.create_secure_cookie(data)

    def get_secure_cookie(self, key=None, load=False):
        """Returns a secure cookie. Cookies get through this method are tracked
        and automatically saved at the end of request if they change.

        :param key:
            Cookie unique name.
        :param load:
            ``True`` to try to load an existing cookie from the request. If it
            is not set, a clean secure cookie is returned. ``False`` to return
            a new secure cookie. Default is ``False``.
        :return:
            A ``werkzeug.contrib.SecureCookie`` instance.
        """
        if key not in self._data:
            if load:
                self._data[key] = self.load_secure_cookie(key)
            else:
                self._data[key] = self.create_secure_cookie()

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
                                        secret_key=self.provider.secret_key)

    def create_secure_cookie(self, data=None):
        """Returns a new secure cookie.

        This cookie must be saved using a response object at the end of a
        request. To get a cookie that is saved automatically, use
        :meth:`SessionStore.get_secure_cookie`.

        :param data:
            A dictionary to be loaded into the secure cookie. If set, the
            secure cookie will be marked as modified.
        :return:
            A ``werkzeug.contrib.SecureCookie`` instance.
        """
        cookie = SecureCookie(data=data, secret_key=self.provider.secret_key)
        if data is not None:
            # Always force it to save when data is passed.
            cookie.modified = True

        return cookie


class Session(db.Model):
    """Stores session data."""
    #: Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    #: Expiration date.
    expires = db.DateTimeProperty(required=True)
    #: Session data, pickled.
    data = PickleProperty()


class DatastoreSession(ModificationTrackingDict):
    """A dictionary-like object with values loaded from datastore."""
    def __init__(self, provider=None, secure_cookie=None):
        self.provider = provider
        self.cookie = secure_cookie
        self.entity = None
        ModificationTrackingDict.__init__(self, self._get_data() or ())

    @property
    def sid(self):
        return self.cookie.get('sid', None)

    @property
    def should_save(self):
        """``True`` if the session should be saved."""
        return self.modified

    def get_entity(self):
        if self.sid is None:
            return None

        return Session.get_by_key_name(self.sid)

    def _get_data(self):
        if self.sid is None:
            return None

        data = memcache.get(self.sid, namespace=self.__class__.__name__)

        if data is None:
            self.entity = self.get_entity()
            if self.entity:
                # TODO: check expiration date.
                data = self.entity.data

        if data is None:
            del self.cookie['sid']

        return data

    def delete_entity(self):
        if self.sid is not None:
            memcache.delete(self.sid, namespace=self.__class__.__name__)

            if not self.entity:
                self.entity = self.get_entity()

            if self.entity:
                db.delete(self.entity)
                del self.cookie['sid']
                self.entity = None

    def save_cookie(self, response, key, **kwargs):
        if self.should_save:
            data = dict(self)

            if self.sid is None:
                self.cookie['sid'] = generate_key(self.provider.secret_key)

            if self.entity is None:
                self.entity = Session(key_name=self.sid, data=data)
            else:
                self.entity.data = data

            self.entity.put()
            memcache.set(self.sid, data, namespace=self.__class__.__name__)

        self.cookie.save_cookie(response, key=key, **kwargs)


class DatastoreSessionStore(SessionStore):
    """A session store that uses the datastore for storage. Additionally
    provides signed flash messages and secure cookies that persist
    automatically.
    """
    def _get_session(self, key):
        """Returns a session for a given key. This is the session factory
        method.

        :param key:
            Cookie unique name. If not provided, uses the
            ``session_cookie_name`` value configured for this module.
        :return:
            A dictionary-like session object.
        """
        cookie = self.load_secure_cookie(key)
        return DatastoreSession(provider=self.provider, secure_cookie=cookie)

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
            session.delete_entity()
