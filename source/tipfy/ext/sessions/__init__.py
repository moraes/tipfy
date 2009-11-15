# -*- coding: utf-8 -*-
"""
    tipfy.ext.sessions
    ~~~~~~~~~~~~~~~~~~

    Sessions extension.

    Parts of this file derive from Kay.

    :copyright: (c) 2009 Accense Technology, Inc. All rights reserved.
    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import re
import string
from datetime import datetime, timedelta
from random import choice

from google.appengine.api import memcache
from google.appengine.ext import db

from werkzeug.contrib.securecookie import SecureCookie
from werkzeug.contrib.sessions import SessionStore

from tipfy import local, InternalServerError
from tipfy.ext.model import model_from_protobuf, model_to_protobuf, \
    retry_on_timeout, PickleProperty


KEY_CHARS = string.ascii_letters + string.digits
KEY_RE = re.compile(r'^[a-zA-Z0-9]{64}$')


class Session(db.Model):
    """Stores session data."""
    # Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    # Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    # Expiration date.
    expiration = db.DateTimeProperty(required=True)
    # Session data, pickled.
    data = PickleProperty()
    # User name, in case this session is related to an authenticated user.
    username = db.StringProperty(required=False)


class DatastoreSessionStore(SessionStore):
    def generate_key(self, salt=None):
        """Generates a new session key."""
        return ''.join(choice(KEY_CHARS) for n in xrange(64))

    def is_valid_key(self, key):
        """Checks if a key has the correct format."""
        return KEY_RE.match(key) is not None

    def _is_valid_entity(self, entity):
        """Checks if a session data entity fetched from datastore is valid."""
        if entity.expiration < datetime.now():
            return False

        return True

    def _get_from_datastore(self, sid):
        pb = memcache.get(sid, namespace=self.__class__.__name__)
        if pb is not None:
            entity = model_from_protobuf(pb)
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
        entity = Session(key_name=session.sid, expiration=datetime.now() +
            timedelta(seconds=local.app.config.session_expiration),
            data=dict(session))
        entity.put()

        memcache.set(session.sid, model_to_protobuf(entity),
            namespace=self.__class__.__name__)

    @retry_on_timeout(retries=3, interval=0.2)
    def delete(self, session):
        """Deletes a session."""
        entity = Session.get_by_key_name(session.sid)
        if entity:
            entity.delete()


class SecureCookieSessionStore(SessionStore):
    """A session store class that stores data in secure cookies."""
    def __init__(self, cookie_name):
        self.cookie_name = cookie_name
        self.secret_key = local.app.config.session_secret_key

    def new(self):
        return self.get(None)

    def get(self, sid):
        return SecureCookie.load_cookie(local.request, key=self.cookie_name,
            secret_key=self.secret_key)

    def save(self, session):
        session.save_cookie(local.response, key=self.cookie_name)

    def delete(self, session):
        for key in session.keys():
            del session[key]


class SecureCookieSessionMiddleware(object):
    """Enables sessions using secure cookies."""
    def __init__(self):
        cookie_name = getattr(local.app.config, 'session_cookie_name',
            'tipfy.session')
        self.session_store = SecureCookieSessionStore(cookie_name)

    def process_request(self, request):
        request.session = self.session_store.get(None)

    def process_response(self, request, response):
        if hasattr(request, 'session'):
            self.session_store.save_if_modified(request.session)

        return response


class DatastoreSessionMiddleware(object):
    """Enables sessions using the datastore."""
    def __init__(self):
        # The session id is stored in a secure cookie.
        cookie_name = getattr(local.app.config, 'session_id_cookie_name',
            'tipfy.session_id')
        self.securecookie_store = SecureCookieSessionStore(cookie_name)
        self.session_store = DatastoreSessionStore()

    def process_request(self, request):
        request.session_id = self.securecookie_store.get(None)
        sid = request.session_id.get('_sid', None)
        request.session = self.session_store.get(sid)

    def process_response(self, request, response):
        if hasattr(request, 'session'):
            request.session_id['_sid'] = request.session.sid
            self.session_store.save_if_modified(request.session)
            self.securecookie_store.save_if_modified(request.session_id)

        return response
