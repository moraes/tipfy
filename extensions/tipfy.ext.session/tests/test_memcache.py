# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.session memcache backend
"""
import unittest

from nose.tools import raises
from gaetestbed import DataStoreTestCase, MemcacheTestCase

from google.appengine.api import memcache

from tipfy.ext.session import (MemcacheSessionBackend, Session)


class TestMemcacheSessionBackend(DataStoreTestCase, MemcacheTestCase,
    unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)

    def test_get_without_sid(self):
        session_store = MemcacheSessionBackend()
        session = session_store.get()
        assert isinstance(session, Session)
        assert session == {}

    def test_get_with_invalid_sid(self):
        session_store = MemcacheSessionBackend()
        session = session_store.get('a')
        assert isinstance(session, Session)
        assert session == {}

    def test_get_with_non_existent_sid(self):
        session_store = MemcacheSessionBackend()
        session = session_store.get('a' * 40)
        assert isinstance(session, Session)
        assert session == {}

    def test_save(self):
        session_store = MemcacheSessionBackend()
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
        session_store = MemcacheSessionBackend()
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
