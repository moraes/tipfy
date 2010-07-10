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

    def test_delete_by_sid(self):
        sid = 'test'
        entity = SessionModel.create(sid, {'foo': 'bar', 'baz': 'ding'})
        entity.put()

        cached_data = SessionModel.get_cache(sid)
        assert cached_data is not None

        DatastoreSession.delete_by_sid('test')

        cached_data = SessionModel.get_cache(sid)
        assert cached_data is None
