# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.session datastore backend
"""
from datetime import datetime, timedelta
import unittest

from nose.tools import raises
from gaetestbed import DataStoreTestCase, MemcacheTestCase

from google.appengine.api import memcache
from google.appengine.ext import db

from tipfy import Tipfy
from tipfy.ext.session import (DatastoreSession, DatastoreSessionBackend,
    SessionModel)


class TestSessionModel(DataStoreTestCase, MemcacheTestCase,
    unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)
        self.app = Tipfy()

    def test_get_by_sid_without_cache(self):
        session_store = DatastoreSessionBackend()
        session = session_store.get()
        session['foo'] = 'bar'
        session['baz'] = 'ding'
        session_store.save(session)

        cached_data = SessionModel.get_cache(session.sid)
        assert cached_data is not None

        session.entity.delete_cache()
        cached_data = SessionModel.get_cache(session.sid)
        assert cached_data is None

        entity = SessionModel.get_by_sid(session.sid)
        assert entity is not None
        assert 'foo' in entity.data
        assert 'baz' in entity.data
        assert entity.data['foo'] == 'bar'
        assert entity.data['baz'] == 'ding'

    def test_get_by_sid_invalid(self):
        session_store = DatastoreSessionBackend()
        session = session_store.get()
        session['foo'] = 'bar'
        session['baz'] = 'ding'
        session_store.save(session)

        entity = SessionModel.get_by_sid(session.sid)
        assert entity is not None
        assert 'foo' in entity.data
        assert 'baz' in entity.data
        assert entity.data['foo'] == 'bar'
        assert entity.data['baz'] == 'ding'

        # Set expiration 10 minutes in the past.
        self.app.config.update('tipfy.ext.session',
            {'cookie_session_expires': 600})
        assert self.app.config.get('tipfy.ext.session',
            'cookie_session_expires') == 600

        def get_by_key_name_wrapper(old_get_by_key_name):
            @classmethod
            def get_by_key_name(cls, key_name):
                res = old_get_by_key_name(key_name)
                if res:
                    res.created = datetime.now() - timedelta(seconds=86400)

                return res

            return get_by_key_name

        # Patch to set a old created date.
        SessionModel.get_by_key_name = get_by_key_name_wrapper(
            SessionModel.get_by_key_name)

        entity = SessionModel.get_by_sid(session.sid)
        self.assertEqual(entity, None)
        assert entity is None


class TestDatastoreSessionBackend(DataStoreTestCase, MemcacheTestCase,
    unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)
        self.app = Tipfy()

    def test_get_without_sid(self):
        session_store = DatastoreSessionBackend()
        session = session_store.get()
        assert isinstance(session, DatastoreSession)
        assert session == {}

    def test_get_with_invalid_sid(self):
        session_store = DatastoreSessionBackend()
        session = session_store.get('a')
        assert isinstance(session, DatastoreSession)
        assert session == {}

    def test_get_with_non_existent_sid(self):
        session_store = DatastoreSessionBackend()
        session = session_store.get('a' * 40)
        assert isinstance(session, DatastoreSession)
        assert session == {}

    def test_save(self):
        session_store = DatastoreSessionBackend()
        session = session_store.get()
        session['foo'] = 'bar'
        session['baz'] = 'ding'
        session_store.save(session)

        new_session = session_store.get(session.sid)
        assert 'foo' in session
        assert 'baz' in session
        assert session['foo'] == 'bar'
        assert session['baz'] == 'ding'

    def test_delete(self):
        session_store = DatastoreSessionBackend()
        session = session_store.get()
        session['foo'] = 'bar'
        session['baz'] = 'ding'
        session_store.save(session)

        new_session = session_store.get(session.sid)
        assert 'foo' in session
        assert 'baz' in session
        assert session['foo'] == 'bar'
        assert session['baz'] == 'ding'

        session_store.delete(session)
        new_session = session_store.get(session.sid)
        assert 'foo' not in new_session
        assert 'baz' not in new_session
        assert new_session == {}
