# -*- coding: utf-8 -*-
"""
    sessions
    ========

    Lightweight sessions support for tipfy. Includes sessions using secure
    cookies and supports flash messages.

    :copyright: 2010 by tipfy.org.
    :license: Apache Sotware License, see LICENSE for details.
"""
import base64
import hashlib
import hmac
import logging
import time

from tipfy import DEFAULT_VALUE, REQUIRED_VALUE
from tipfy.utils import json_encode, json_decode

from werkzeug import cached_property
from werkzeug.contrib.sessions import ModificationTrackingDict

#: Default configuration values for this module. Keys are:
#:
#: secret_key
#:     Secret key to generate session cookies. Set this to something random
#:     and unguessable. Default is :data:`tipfy.REQUIRED_VALUE` (an exception
#:     is raised if it is not set).
#:
#: cookie_name
#:     Name of the cookie to save a session or session id. Default is
#:     `tipfy.session`.
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
    'cookie_name':     'tipfy.session',
    'session_max_age': None,
    'cookie_args': {
        'max_age':     None,
        'domain':      None,
        'path':        '/',
        'secure':      None,
        'httponly':    False,
    }
}


class SecureCookie(object):
    """Encapsulates getting and setting secure cookies.

    Extracted from `Tornado`_ and modified.
    """
    def __init__(self, secret_key):
        """
        :param secret_key:
            A long, random sequence of bytes to be used as the HMAC secret
            for the cookie signature.
        """
        self.secret_key = secret_key

    def get_cookie(self, request, name, max_age=None):
        """Returns the given signed cookie if it validates, or None."""
        value = request.cookies.get(name)

        if not value:
            return None

        parts = value.split('|')
        if len(parts) != 3:
            return None

        signature = self._get_signature(name, parts[0], parts[1])

        if not self._check_signature(parts[2], signature):
            logging.warning('Invalid cookie signature %r', value)
            return None

        if max_age is not None and (int(parts[1]) < time.time() - max_age):
            logging.warning('Expired cookie %r', value)
            return None

        try:
            return self._decode(parts[0])
        except:
            return None

    def set_cookie(self, response, name, value, **kwargs):
        """Signs and timestamps a cookie so it cannot be forged.

        To read a cookie set with this method, use get_cookie().
        """
        value = self.get_signed_value(name, value)
        response.set_cookie(name, value, **kwargs)

    def get_signed_value(self, name, value):
        timestamp = str(int(time.time()))
        value = self._encode(value)
        signature = self._get_signature(name, value, timestamp)
        return '|'.join([value, timestamp, signature])

    def _encode(self, value):
        return base64.b64encode(json_encode(value, separators=(',',':')))

    def _decode(self, value):
        return json_decode(base64.b64decode(value))

    def _get_signature(self, *parts):
        hash = hmac.new(self.secret_key, digestmod=hashlib.sha1)
        hash.update('|'.join(parts))
        return hash.hexdigest()

    def _check_signature(self, a, b):
        if len(a) != len(b):
            return False

        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)

        return result == 0


class DatastoreSession(ModificationTrackingDict):
    @classmethod
    def get_session(cls, store, name, **kwargs):
        """TODO"""
        raise NotImplementedError()

    def save_session(self, store, name, **kwargs):
        """TODO"""
        raise NotImplementedError()


class MemcacheSession(ModificationTrackingDict):
    @classmethod
    def get_session(cls, store, name, **kwargs):
        """TODO"""
        raise NotImplementedError()

    def save_session(self, store, name, **kwargs):
        """TODO"""
        raise NotImplementedError()


class SecureCookieSession(ModificationTrackingDict):
    @classmethod
    def get_session(cls, store, name, **kwargs):
        return cls(store.get_secure_cookie(name) or ())

    def save_session(self, store, response, name, **kwargs):
        if self.modified:
            store.set_secure_cookie(response, name, self, **kwargs)


class SessionStore(object):
    #: A dictionary with the default supported backends.
    default_backends = {
        #'datastore':    DatastoreSession,
        #'memcache':     MemcacheSession,
        'securecookie': SecureCookieSession,
    }

    def __init__(self, app, backends=None, default_backend='securecookie'):
        self.app = app
        self.request = app.request
        # A dictionary of support backend classes.
        self.backends = backends or self.default_backends
        # The default backend to use when none is provided.
        self.default_backend = default_backend
        # Base configuration.
        self.config = app.get_config(__name__)
        # Tracked sessions.
        self._sessions = {}

    @cached_property
    def secure_cookie_factory(self):
        """Factory for secure cookies."""
        return SecureCookie(self.app.get_config(__name__, 'secret_key'))

    def get_session(self, key=None, backend=None, **kwargs):
        """Returns a session for a given key. If the session doesn't exist, a
        new session is returned.

        :param key:
            Cookie unique name. If not provided, uses the ``cookie_name``
            value configured for this module.
        :param kwargs:
            Keyword arguments to set the session cookie. Keys are the same
            that can be passed to ``Response.set_cookie``. If not set, use
            the ``cookie_args`` values configured for this module.
        :returns:
            A dictionary-like session object.
        """
        key = key or self.config['cookie_name']
        backend = backend or self.default_backend
        sessions = self._sessions.setdefault(backend, {})

        if key not in sessions:
            if not kwargs:
                kwargs = self.config['cookie_args'].copy()

            value = self.backends[backend].get_session(self, key, **kwargs)
            self._sessions[backend][key] = (value, kwargs)

        return self._sessions[backend][key][0]

    def set_session(self, key, value, backend=None, **kwargs):
        backend = backend or self.default_backend
        if not kwargs:
            kwargs = self.config['cookie_args'].copy()

        self._sessions[backend][key] = (value, kwargs)

    def get_secure_cookie(self, name, max_age=DEFAULT_VALUE):
        if max_age is DEFAULT_VALUE:
            max_age = self.config['session_max_age']

        return self.secure_cookie_factory.get_cookie(self.request, name,
            max_age=max_age)

    def set_secure_cookie(self, response, name, value, **kwargs):
        assert isinstance(value, dict), 'SecureCookie values must be a dict.'
        if not kwargs:
            kwargs = self.config['cookie_args'].copy()

        self.secure_cookie_factory.set_cookie(response, name, value, **kwargs)

    def get_flash(self, key=None, backend=None, flash_key='_flash', **kwargs):
        """Returns a flash message. Flash messages are deleted when first read.

        :param key:
            Cookie unique name.
        :param kwargs:
            Options to save the cookie. See :meth:`SessionStore.get_session`.
        :returns:
            The data stored in the flash, or an empty list.
        """
        session = self.get_session(key=key, backend=backend, **kwargs)
        return session.pop(flash_key, [])

    def set_flash(self, data, key=None, backend=None, flash_key='_flash',
        **kwargs):
        """Sets a flash message. Flash messages are deleted when first read.

        :param data:
            Dictionary to be saved in the flash message.
        :param key:
            Cookie unique name.
        :param kwargs:
            Options to save the cookie. See :meth:`SessionStore.get_session`.
        :returns:
            None.
        """
        session = self.get_session(key=key, backend=backend, **kwargs)
        session.setdefault(flash_key, []).append(data)

    def save_sessions(self, response):
        """Saves all sessions to a response object."""
        if not self._sessions:
            return

        for sessions in self._sessions.values():
            for key, (value, kwargs) in sessions.iteritems():
                value.save_session(self, response, key, **kwargs)

    @classmethod
    def factory(cls, _app, _name, **kwargs):
        if _name not in _app.request.registry:
            _app.request.registry[_name] = cls(_app, **kwargs)

        return _app.request.registry[_name]
