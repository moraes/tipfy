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
from tipfy.ext.sharded_counter import Counter


class TestCounter(DataStoreTestCase, MemcacheTestCase,
    unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)
        self.app = Tipfy({
            'tipfy.ext.sharded_counter': {
                'shards': 10,
            },
        })

    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_counter(self):
        # Build a new counter that uses the unique key name 'hits'.
        hits = Counter('hits')

        assert hits.count == 0

        # Increment by 1.
        hits.increment()
        # Increment by 10.
        hits.increment(10)
        # Decrement by 3.
        hits.increment(-3)
        # This is the current count.
        assert hits.count == 8

        # Forces fetching a non-cached count of all shards.
        assert hits.get_count(nocache=True) == 8

        # Set the counter to an arbitrary value.
        hits.count = 6

        assert hits.get_count(nocache=True) == 6

    def test_cache(self):
        # Build a new counter that uses the unique key name 'hits'.
        hits = Counter('hits')

        assert hits.count == 0

        # Increment by 1.
        hits.increment()
        # Increment by 10.
        hits.increment(10)
        # Decrement by 3.
        hits.increment(-3)
        # This is the current count.
        assert hits.count == 8

        # Forces fetching a non-cached count of all shards.
        assert hits.get_count(nocache=True) == 8

        # Set the counter to an arbitrary value.
        hits.delete()

        assert hits.get_count() == 8
        assert hits.get_count(nocache=True) == 0

        hits.memcached.delete_count()

        assert hits.get_count() == 0
