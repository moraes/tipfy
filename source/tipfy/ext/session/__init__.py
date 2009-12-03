# -*- coding: utf-8 -*-
"""
    tipfy.ext.session
    ~~~~~~~~~~~~~~~~~

    Session extension.

    This module provides sessions using secure cookies or the datastore.

    .. note::
       The session implementations are still pretty new and untested.
       Consider this as a work in progress.

    This module derives from `Kay`_.

    :copyright: (c) 2009 Accense Technology, Inc. All rights reserved.
    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime, timedelta

from google.appengine.api import memcache
from google.appengine.ext import db

from werkzeug.contrib.securecookie import SecureCookie
from werkzeug.contrib.sessions import SessionStore

from tipfy import local, get_config
from tipfy.ext.db import get_entity_from_protobuf, get_protobuf_from_entity, \
    retry_on_timeout, PickleProperty

#: Default configuration values for this module. Keys are:
#: A dictionary of configuration options for ``tipfy.ext.session``. Keys are:
#:   - ``secret_key``: Secret key to generate session cookies. Set this to
#:     something random and unguessable. Default is
#:     `please-change-me-it-is-important`.
#:   - ``expiration``: Session expiration time in seconds. Default is `86400`.
#:   - ``cookie_name``: Name of the cookie to save the session. Default is
#:     `tipfy.session`.
#:   - ``id_cookie_name``:Name of the cookie to save the session id. Default is
#:     `tipfy.session_id`.
default_config = {
    'secret_key': 'please-change-me-it-is-important',
    'expiration': 86400,
    'cookie_name': 'tipfy.session',
    'id_cookie_name': 'tipfy.session_id',
}

# Proxies to the session variables set on each request.
local.session = local.session_store = None
session, session_store = local('session'), local('session_store')


def set_datastore_session(app=None):
    """Hook to initialize and persist datastore based sessions. This
    initializes :class:`DatastoreSessionMiddleware` and sets hooks to load and
    save sessions.

    To enable it, add a hook to the list of hooks in ``config.py``:

    .. code-block:: python

       config = {
           'tipfy': {
               'hooks': {
                   'pos_init_app': ['tipfy.ext.session:set_datastore_session'],
                   # ...
               },
           },
       }

    :param app:
        A :class:`tipfy.WSGIApplication` instance.
    :return:
        ``None``.
    """
    middleware = DatastoreSessionMiddleware()
    app.hooks.add('pre_dispatch_handler', middleware.load_session)
    app.hooks.add('pre_send_response', middleware.save_session)


def set_securecookie_session(app=None):
    """Hook to initialize and persist secure cookie based sessions. This
    initializes :class:`SecureCookieSessionMiddleware` and sets hooks to load
    and save sessions.

    To enable it, add a hook to the list of hooks in ``config.py``:

    .. code-block:: python

       config = {
           'tipfy': {
               'hooks': {
                   'pos_init_app': ['tipfy.ext.session:set_securecookie_session'],
                   # ...
               },
           },
       }

    :param app:
        A :class:`tipfy.WSGIApplication` instance.
    :return:
        ``None``.
    """
    middleware = SecureCookieSessionMiddleware()
    app.hooks.add('pre_dispatch_handler', middleware.load_session)
    app.hooks.add('pre_send_response', middleware.save_session)


class DatastoreSessionMiddleware(object):
    """Enables sessions using the datastore."""
    def __init__(self):
        # The session id is stored in a secure cookie.
        self.session_id_store = SecureCookieSessionStore(
            get_config(__name__, 'id_cookie_name'))
        self.session_store = DatastoreSessionStore()

    def load_session(self, request=None, app=None):
        self.session_id = self.session_id_store.get(None)
        local.session_store = self.session_store
        local.session = self.session_store.get(self.session_id.get('_sid'))

    def save_session(self, request=None, response=None, app=None):
        if hasattr(local, 'session'):
            self.session_id['_sid'] = local.session.sid
            self.session_store.save_if_modified(local.session)
            self.session_id_store.save_if_modified(self.session_id)

        return response


class SecureCookieSessionMiddleware(object):
    """Enables sessions using secure cookies."""
    def __init__(self):
        self.session_store = SecureCookieSessionStore(get_config(__name__,
            'cookie_name'))

    def load_session(self, request=None, app=None):
        local.session_store = self.session_store
        local.session = self.session_store.get(None)

    def save_session(self, request=None, response=None, app=None):
        if hasattr(local, 'session'):
            self.session_store.save_if_modified(local.session)

        return response


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
    #: User name, in case this session is related to an authenticated user.
    username = db.StringProperty(required=False)


class DatastoreSessionStore(SessionStore):
    def __init__(self, expires=None):
        SessionStore.__init__(self)
        self.expires = expires or get_config(__name__, 'expiration')

    def _is_valid_entity(self, entity):
        """Checks if a session data entity fetched from datastore is valid."""
        if entity.expires < datetime.now():
            return False

        return True

    def _get_from_datastore(self, sid):
        pb = memcache.get(sid, namespace=self.__class__.__name__)
        if pb is not None:
            entity = get_entity_from_protobuf(pb)
        else:
            entity = Session.get_by_key_name(sid)

        return entity

    def get(self, sid):
        """Returns a session given a session id, or creates a new one."""
        entity = None
        if sid and self.is_valid_key(sid):
            entity = self._get_from_datastore(sid)

        if entity is None or not self._is_valid_entity(entity):
            return self.new()

        return self.session_class(entity.data, sid, False)

    @retry_on_timeout(retries=3, interval=0.2)
    def save(self, session):
        """Saves a session."""
        entity = Session(key_name=session.sid, expires=datetime.now() + \
            timedelta(seconds=self.expires), data=dict(session))
        entity.put()

        memcache.set(session.sid, get_protobuf_from_entity(entity),
            time=self.expires, namespace=self.__class__.__name__)

    @retry_on_timeout(retries=3, interval=0.2)
    def delete(self, session):
        """Deletes a session."""
        entity = Session.get_by_key_name(session.sid)
        if entity:
            entity.delete()


class SecureCookieSessionStore(SessionStore):
    """A session store class that stores data in secure cookies."""
    def __init__(self, cookie_name, expires=None):
        self.cookie_name = cookie_name
        self.secret_key = get_config(__name__, 'secret_key')
        self.expires = expires or get_config(__name__, 'expiration')

    def new(self):
        return self.get(None)

    def get(self, sid):
        return SecureCookie.load_cookie(local.request, key=self.cookie_name,
            secret_key=self.secret_key)

    def save(self, session):
        session.save_cookie(local.response, key=self.cookie_name, expires=
            datetime.now() + timedelta(seconds=self.expires))

    def delete(self, session):
        for key in session.keys():
            del session[key]
