# -*- coding: utf-8 -*-
"""
    tipfy.ext.session.datastore
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Datastore session extension.

    This module derives from `Kay`_.

    :copyright: (c) 2009 Accense Technology, Inc. All rights reserved.
    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime, timedelta

from google.appengine.api import memcache
from google.appengine.ext import db

from werkzeug.contrib.sessions import SessionStore

from tipfy import local, get_config
from tipfy.ext.session.securecookie import SecureCookieSessionStore
from tipfy.ext.db import get_entity_from_protobuf, get_protobuf_from_entity, \
    retry_on_timeout, PickleProperty

# Let other modules initialize sessions.
_is_ext_set = False
# The module name from where we get configuration values.
EXT = 'tipfy.ext.session'


def setup(app):
    """
    Setup this extension.

    This will set hooks to initialize and persist datastore based sessions. This
    initializes :class:`DatastoreSessionMiddleware` and sets hooks to load and
    save sessions.

    To enable it, add this module to the list of extensions in ``config.py``:

    .. code-block:: python

       config = {
           'tipfy': {
               'extensions': [
                   'tipfy.ext.session.datastore',
                   # ...
               ],
           },
       }

    :param app:
        The WSGI application instance.
    :return:
        ``None``.
    """
    global _is_ext_set
    if _is_ext_set is False:
        middleware = DatastoreSessionMiddleware()
        app.hooks.add('pre_dispatch_handler', middleware.load_session)
        app.hooks.add('post_dispatch_handler', middleware.save_session)
        _is_ext_set = True


class DatastoreSessionMiddleware(object):
    """Handles sessions using the datastore."""
    def __init__(self):
        # The session id is stored in a secure cookie.
        self.session_id_store = SecureCookieSessionStore(
            get_config(EXT, 'id_cookie_name'))
        self.session_store = DatastoreSessionStore()

    def load_session(self):
        self.session_id = self.session_id_store.get(None)
        local.session_store = self.session_store
        local.session = self.session_store.get(self.session_id.get('_sid'))

    def save_session(self, response):
        if hasattr(local, 'session'):
            self.session_id['_sid'] = local.session.sid
            self.session_store.save_if_modified(local.session)
            self.session_id_store.save_if_modified(self.session_id)


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
        self.expires = expires or get_config(EXT, 'expiration')

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
