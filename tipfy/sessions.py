# -*- coding: utf-8 -*-
"""
    tipfy.sessions
    ==============

    Lightweight sessions support for tipfy. Includes sessions using secure
    cookies and supports flash messages. For App Engine's datastore and
    memcache based sessions, see tipfy.appengine.sessions.

    :copyright: 2011 by tipfy.org.
    :license: Apache Sotware License, see LICENSE for details.
"""
import hashlib
import hmac
import logging
import time

from tipfy import APPENGINE, DEFAULT_VALUE, REQUIRED_VALUE
from tipfy.json import json_b64encode, json_b64decode

from werkzeug.utils import cached_property
from werkzeug.contrib.sessions import ModificationTrackingDict

#: Default configuration values for this module. Keys are:
#:
#: secret_key
#:     Secret key to generate session cookies. Set this to something random
#:     and unguessable. Default is :data:`tipfy.REQUIRED_VALUE` (an exception
#:     is raised if it is not set).
#:
#: default_backend
#:     The default backend to use when none is provided. Default is
#:     `securecookie`.
#:
#: cookie_name
#:     Name of the cookie to save a session or session id. Default is
#:     `session`.
#:
#: session_max_age:
#:     Default session expiration time in seconds. Limits the duration of the
#:     contents of a cookie, even if a session cookie exists. If None, the
#:     contents lasts as long as the cookie is valid. Default is None.
#:
#: cookie_args
#:     Default keyword arguments used to set a cookie. Keys are:
#:
#:     - max_age: Cookie max age in seconds. Limits the duration
#:       of a session cookie. If None, the cookie lasts until the client
#:       is closed. Default is None.
#:
#:     - domain: Domain of the cookie. To work accross subdomains the
#:       domain must be set to the main domain with a preceding dot, e.g.,
#:       cookies set for `.mydomain.org` will work in `foo.mydomain.org` and
#:       `bar.mydomain.org`. Default is None, which means that cookies will
#:       only work for the current subdomain.
#:
#:     - path: Path in which the authentication cookie is valid.
#:       Default is `/`.
#:
#:     - secure: Make the cookie only available via HTTPS.
#:
#:     - httponly: Disallow JavaScript to access the cookie.
default_config = {
    'secret_key':      REQUIRED_VALUE,
    'default_backend': 'securecookie',
    'cookie_name':     'session',
    'session_max_age': None,
    'cookie_args': {
        'max_age':     None,
        'domain':      None,
        'path':        '/',
        'secure':      None,
        'httponly':    False,
    }
}


class SecureCookieSerializer(object):
    """Serializes and deserializes secure cookie values.

    Extracted from `Tornado`_ and modified.
    """
    def __init__(self, secret_key):
        """Initiliazes the serializer/deserializer.

        :param secret_key:
            A long, random sequence of bytes to be used as the HMAC secret
            for the cookie signature.
        """
        self.secret_key = secret_key

    def serialize(self, name, value):
        """Serializes a signed cookie value.

        :param name:
            Cookie name.
        :param value:
            Cookie value to be serialized.
        :returns:
            A serialized value ready to be stored in a cookie.
        """
        timestamp = str(self.get_timestamp())
        value = self.encode(value)
        signature = self._get_signature(name, value, timestamp)
        return '|'.join([value, timestamp, signature])

    def deserialize(self, name, value, max_age=None):
        """Deserializes a signed cookie value.

        :param name:
            Cookie name.
        :param value:
            A cookie value to be deserialized.
        :param max_age:
            Maximum age in seconds for a valid cookie. If the cookie is older
            than this, returns None.
        :returns:
            The deserialized secure cookie, or None if it is not valid.
        """
        if not value:
            return

        parts = value.split('|')
        if len(parts) != 3:
            return

        signature = self._get_signature(name, parts[0], parts[1])

        if not self._check_signature(parts[2], signature):
            logging.warning('Invalid cookie signature %r', value)
            return

        if max_age is not None:
            if int(parts[1]) < self.get_timestamp() - max_age:
                logging.warning('Expired cookie %r', value)
                return

        try:
            return self.decode(parts[0])
        except Exception, e:
            logging.warning('Cookie value failed to be decoded: %r', parts[0])

    def encode(self, value):
        return json_b64encode(value)

    def decode(self, value):
        return json_b64decode(value)

    def get_timestamp(self):
        return int(time.time())

    def _get_signature(self, *parts):
        """Generates an HMAC signature."""
        signature = hmac.new(self.secret_key, digestmod=hashlib.sha1)
        signature.update('|'.join(parts))
        return signature.hexdigest()

    def _check_signature(self, a, b):
        """Checks if an HMAC signature is valid."""
        if len(a) != len(b):
            return False

        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)

        return result == 0


class SessionDict(ModificationTrackingDict):
    __slots__ = ModificationTrackingDict.__slots__ + ('new',)

    def __init__(self, data=None, new=False):
        ModificationTrackingDict.__init__(self, data or ())
        self.new = new

    def get_flashes(self, key='_flash'):
        """Returns a flash message. Flash messages are deleted when first read.

        :param key:
            Name of the flash key stored in the session. Default is '_flash'.
        :returns:
            The data stored in the flash, or an empty list.
        """
        if key not in self:
            # Avoid popping if the key doesn't exist to not modify the session.
            return []

        return self.pop(key, [])

    def add_flash(self, value, level=None, key='_flash'):
        """Adds a flash message. Flash messages are deleted when first read.

        :param value:
            Value to be saved in the flash message.
        :param level:
            An optional level to set with the message. Default is `None`.
        :param key:
            Name of the flash key stored in the session. Default is '_flash'.
        """
        self.setdefault(key, []).append((value, level))

    #: Alias, Flask-like interface.
    flash = add_flash


class BaseSessionFactory(object):
    def __init__(self, name, session_store):
        self.name = name
        self.session_store = session_store
        self.session_args = session_store.config['cookie_args'].copy()
        self.session = None


class CookieSessionFactory(BaseSessionFactory):
    """A session that stores data serialized in a ordinary cookie."""
    def save_session(self, response):
        if self.session is None:
            path = self.session_args.get('path', '/')
            domain = self.session_args.get('domain', None)
            response.delete_cookie(self.name, path=path, domain=domain)
        else:
            response.set_cookie(self.name, self.session, **self.session_args)


class SecureCookieSessionFactory(BaseSessionFactory):
    """A session that stores data serialized in a signed cookie."""
    session_class = SessionDict

    def get_session(self, max_age=DEFAULT_VALUE):
        if self.session is None:
            data = self.session_store.get_secure_cookie(self.name,
                                                        max_age=max_age)
            new = data is None
            self.session = self.session_class(self, data=data, new=new)

        return self.session

    def save_session(self, response):
        if self.session is None or not self.session.modified:
            return

        self.session_store.save_secure_cookie(
            response, self.name, dict(self.session), **self.session_args)


class SessionStore(object):
    def __init__(self, request):
        self.request = request
        # Base configuration.
        self.config = request.app.config[__name__]
        # Tracked sessions.
        self.sessions = {}
        # Serializer and deserializer for signed cookies.
        self.cookie_serializer = SecureCookieSerializer(
            self.config['secret_key'])

    # Backend based sessions --------------------------------------------------

    def _get_session_container(self, name, factory):
        if name not in self.sessions:
            self.sessions[name] = factory(name, self)

        return self.sessions[name]

    def get_session(self, name=None, max_age=DEFAULT_VALUE,
                    factory=SecureCookieSessionFactory):
        """Returns a session for a given name. If the session doesn't exist, a
        new session is returned.

        :param name:
            Cookie name. If not provided, uses the ``cookie_name``
            value configured for this module.
        :returns:
            A dictionary-like session object.
        """
        name = name or self.config['cookie_name']

        if max_age is DEFAULT_VALUE:
            max_age = self.config['session_max_age']

        container = self._get_session_container(name, factory)
        return container.get_session(max_age=max_age)

    # Signed cookies ----------------------------------------------------------

    def get_secure_cookie(self, name, max_age=DEFAULT_VALUE):
        """Returns a deserialized secure cookie value.

        :param name:
            Cookie name.
        :param max_age:
            Maximum age in seconds for a valid cookie. If the cookie is older
            than this, returns None.
        :returns:
            A secure cookie value or None if it is not set.
        """
        if max_age is DEFAULT_VALUE:
            max_age = self.config['session_max_age']

        value = self.request.cookies.get(name)
        if value:
            return self.cookie_serializer.deserialize(name, value,
                                                      max_age=max_age)

    def set_secure_cookie(self, name, value, **kwargs):
        """Sets a secure cookie to be saved.

        :param name:
            Cookie name.
        :param value:
            Cookie value. Must be a dictionary.
        :param kwargs:
            Options to save the cookie. See :meth:`get_session`.
        """
        container = self._get_session_container(name,
                                                SecureCookieSessionFactory)
        container.session = value
        container.session_args.update(kwargs)

    # Ordinary cookies --------------------------------------------------------

    def get_cookie(self, name, decoder=json_b64decode):
        """Returns a cookie from the request, decoding it.

        :param name:
            Cookie name.
        :param decoder:
            An decoder for the cookie value. Default is
            func:`tipfy.json.json_b64decode`.
        :returns:
            A decoded cookie value, or None if a cookie with this name is not
            set or decoding failed.
        """
        value = self.request.cookies.get(name)
        if value is not None and decoder:
            try:
                value = decoder(value)
            except Exception, e:
                return

        return value

    def set_cookie(self, name, value, format=None, encoder=json_b64encode,
        **kwargs):
        """Registers a cookie to be saved or deleted.

        :param name:
            Cookie name.
        :param value:
            Cookie value.
        :param format:
            If set to 'json', the value is serialized to JSON and encoded
            to base64.

            ..warning: Deprecated. Pass an encoder instead.
        :param encoder:
            An encoder for the cookie value. Default is
            func:`tipfy.json.json_b64encode`.
        :param kwargs:
            Options to save the cookie. See :meth:`get_session`.
        """
        if format is not None:
            from warnings import warn
            warn(DeprecationWarning("SessionStore.set_cookie(): the "
                "'format' argument is deprecated. Use 'encoder' instead to "
                "pass an encoder callable."))

            if format == 'json':
                value = json_b64encode(value)
        elif encoder:
            value = encoder(value)

        container = self._get_session_container(name, CookieSessionFactory)
        container.session = value
        container.session_args.update(kwargs)

    def delete_cookie(self, name, **kwargs):
        """Registers a cookie or secure cookie to be deleted.

        :param name:
            Cookie name.
        :param kwargs:
            Options to delete the cookie. See :meth:`get_session`.
        """
        self.set_cookie(name, None, **kwargs)

    def unset_cookie(self, name):
        """Unsets a cookie previously set. This won't delete the cookie, it
        just won't be saved.

        :param name:
            Cookie name.
        """
        self.sessions.pop(name, None)

    # Saving to a response object ---------------------------------------------

    def save_sessions(self, response):
        """Saves all cookies and sessions to a response object.

        :param response:
            A ``tipfy.app.Response`` object.
        """
        for session in self.sessions.values():
            session.save_session(response)
    # Old name
    save = save_sessions

    def save_secure_cookie(self, response, name, value, **kwargs):
        value = self.cookie_serializer.serialize(name, value)
        response.set_cookie(name, value, **kwargs)

    # Deprecated methods ------------------------------------------------------

    def set_session(self, name, value, backend=None, **kwargs):
        """Sets a session value. If a session with the same name exists, it
        will be overriden with the new value.

        :param name:
            Cookie name. See :meth:`get_session`.
        :param value:
            A dictionary of session values.
        :param backend:
            Name of the session backend. See :meth:`get_session`.
        :param kwargs:
            Options to save the cookie. See :meth:`get_session`.
        """
        from warnings import warn
        warn(DeprecationWarning("SessionStore.set_session(): this "
            "method is deprecated. Cookie arguments can be set directly in "
            "a session."))

        self.set_secure_cookie(name, value, **kwargs)

    def update_session_args(self, name, backend=None, **kwargs):
        """Updates the cookie options for a session.

        :param name:
            Cookie name. See :meth:`get_session`.
        :param backend:
            Name of the session backend. See :meth:`get_session`.
        :param kwargs:
            Options to save the cookie. See :meth:`get_session`.
        :returns:
            True if the session was updated, False otherwise.
        """
        from warnings import warn
        warn(DeprecationWarning("SessionStore.update_session_args(): this "
            "method is deprecated. Cookie arguments can be set directly in "
            "a session."))

        if name in self.sessions:
            self.sessions[name].session_args.update(kwargs)
            return True

        return False

    def get_cookie_args(self, **kwargs):
        """Returns a copy of the default cookie configuration updated with the
        passed arguments.

        :param kwargs:
            Keyword arguments to override in the cookie configuration.
        :returns:
            A dictionary with arguments for the session cookie.
        """
        from warnings import warn
        warn(DeprecationWarning("SessionStore.get_cookie_args(): this "
            "method is deprecated. Cookie arguments can be set directly in "
            "a session."))

        _kwargs = self.config['cookie_args'].copy()
        _kwargs.update(kwargs)
        return _kwargs


class SessionMiddleware(object):
    """Saves sessions at the end of a request."""
    def after_dispatch(self, handler, response):
        """Called after the class:`tipfy.RequestHandler` method was executed.

        :param handler:
            A class:`tipfy.RequestHandler` instance.
        :param response:
            A class:`tipfy.Response` instance.
        :returns:
            A class:`tipfy.Response` instance.
        """
        handler.session_store.save(response)
        return response
