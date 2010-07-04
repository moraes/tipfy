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
from tipfy.ext.session import SessionModel, DatastoreSession


class TestSessionModel(DataStoreTestCase, MemcacheTestCase,
    unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)
        self.app = Tipfy()

    def test_get_by_sid_without_cache(self):
        sid = 'test'
        entity = SessionModel.create(sid, {'foo': 'bar', 'baz': 'ding'})
        entity.put()

        cached_data = SessionModel.get_cache(sid)
        assert cached_data is not None

        entity.delete_cache()
        cached_data = SessionModel.get_cache(sid)
        assert cached_data is None

        entity = SessionModel.get_by_sid(sid)
        assert entity is not None
        assert 'foo' in entity.data
        assert 'baz' in entity.data
        assert entity.data['foo'] == 'bar'
        assert entity.data['baz'] == 'ding'

    def test_delete_by_sid_invalid(self):
        sid = 'test'
        entity = SessionModel.create(sid, {'foo': 'bar', 'baz': 'ding'})
        entity.put()

        entity = SessionModel.get_by_sid(sid)
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

        entity = SessionModel.get_by_sid(sid)
        self.assertEqual(entity, None)
        assert entity is None

    def test_delete_by_sid(self):
        sid = 'test'
        entity = SessionModel.create(sid, {'foo': 'bar', 'baz': 'ding'})
        entity.put()

        cached_data = SessionModel.get_cache(sid)
        assert cached_data is not None

        DatastoreSession.delete_by_sid('test')

        cached_data = SessionModel.get_cache(sid)
        assert cached_data is None
