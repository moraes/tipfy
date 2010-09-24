# -*- coding: utf-8 -*-
"""
    Tests for tipfyext.appengine.sharded_counter
"""
from datetime import datetime, timedelta
import unittest
from gaetestbed import DataStoreTestCase, MemcacheTestCase

from google.appengine.api import memcache
from google.appengine.ext import db

from tipfy import Tipfy
from tipfyext.appengine.sharded_counter import Counter


class TestCounter(DataStoreTestCase, MemcacheTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)

        app = Tipfy()
        app.set_locals()

    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_counter(self):
        # Build a new counter that uses the unique key name 'hits'.
        hits = Counter('hits')

        self.assertEqual(hits.count, 0)

        # Increment by 1.
        hits.increment()
        # Increment by 10.
        hits.increment(10)
        # Decrement by 3.
        hits.increment(-3)
        # This is the current count.
        self.assertEqual(hits.count, 8)

        # Forces fetching a non-cached count of all shards.
        self.assertEqual(hits.get_count(nocache=True), 8)

        # Set the counter to an arbitrary value.
        hits.count = 6

        self.assertEqual(hits.get_count(nocache=True), 6)

    def test_cache(self):
        # Build a new counter that uses the unique key name 'hits'.
        hits = Counter('hits')

        self.assertEqual(hits.count, 0)

        # Increment by 1.
        hits.increment()
        # Increment by 10.
        hits.increment(10)
        # Decrement by 3.
        hits.increment(-3)
        # This is the current count.
        self.assertEqual(hits.count, 8)

        # Forces fetching a non-cached count of all shards.
        self.assertEqual(hits.get_count(nocache=True), 8)

        # Set the counter to an arbitrary value.
        hits.delete()

        self.assertEqual(hits.get_count(), 8)
        self.assertEqual(hits.get_count(nocache=True), 0)

        hits.memcached.delete_count()

        self.assertEqual(hits.get_count(), 0)
