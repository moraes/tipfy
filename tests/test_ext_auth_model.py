# -*- coding: utf-8 -*-
"""
    Tests for tipfy.application
"""
import unittest

from nose.tools import raises

from gaetestbed import DataStoreTestCase

import _base

import tipfy
from tipfy import local, WSGIApplication
from tipfy.ext.auth.model import check_password, gen_pwhash, gen_salt, User


class TestUserModel(DataStoreTestCase, unittest.TestCase):
    def setUp(self):
        app = tipfy.WSGIApplication()
        DataStoreTestCase.setUp(self)

    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_create(self):
        user = User.create('my_username', 'my_id')
        assert isinstance(user, User)

        # Second one will fail to be created.
        user = User.create('my_username', 'my_id')
        assert user is None

    def test_create_with_password_hash(self):
        user = User.create('my_username', 'my_id', password_hash='foo')

        assert isinstance(user, User)
        assert user.password == 'foo'

    def test_create_with_password(self):
        user = User.create('my_username', 'my_id', password='foo')

        assert isinstance(user, User)
        assert user.password != 'foo'
        assert len(user.password.split('$')) == 3

    def test_set_password(self):
        user = User.create('my_username', 'my_id', password='foo')
        assert isinstance(user, User)

        password = user.password

        user.set_password('bar')
        assert user.password != password

        assert user.password != 'bar'
        assert len(user.password.split('$')) == 3

    def test_check_password(self):
        app = WSGIApplication()
        user = User.create('my_username', 'my_id', password='foo')

        assert user.check_password('foo') is True
        assert user.check_password('bar') is False

    def test_check_session(self):
        app = WSGIApplication()
        user = User.create('my_username', 'my_id', password='foo')

        session_id = user.session_id
        assert user.check_session(session_id) is True
        assert user.check_session('bar') is False

    def test_get_by_username(self):
        user = User.create('my_username', 'my_id')
        user_1 = User.get_by_username('my_username')

        assert isinstance(user, User)
        assert isinstance(user_1, User)
        assert str(user.key()) == str(user_1.key())

    def test_get_by_auth_id(self):
        user = User.create('my_username', 'my_id')
        user_1 = User.get_by_auth_id('my_id')

        assert isinstance(user, User)
        assert isinstance(user_1, User)
        assert str(user.key()) == str(user_1.key())

    def test_unicode(self):
        user_1 = User(username='Calvin', auth_id='test', session_id='test')
        assert unicode(user_1) == u'Calvin'

    def test_str(self):
        user_1 = User(username='Hobbes', auth_id='test', session_id='test')
        assert str(user_1) == u'Hobbes'

    def test_eq(self):
        user_1 = User(key_name='test', username='Calvin', auth_id='test', session_id='test')
        user_2 = User(key_name='test', username='Calvin', auth_id='test', session_id='test')

        assert user_1 == user_2
        assert user_1 != ''

    def test_ne(self):
        user_1 = User(key_name='test', username='Calvin', auth_id='test', session_id='test')
        user_2 = User(key_name='test_2', username='Calvin', auth_id='test', session_id='test')

        assert user_1 != user_2

    def test_renew_session(self):
        app = WSGIApplication()
        user = User.create('my_username', 'my_id')
        user._renew_session()

    def test_renew_session_force(self):
        app = WSGIApplication()
        user = User.create('my_username', 'my_id')
        user._renew_session(force=True)


class TestMiscelaneous(DataStoreTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        app = tipfy.WSGIApplication()

    def tearDown(self):
        tipfy.local_manager.cleanup()

    @raises(ValueError)
    def test_gen_salt(self):
        gen_salt(0)

    def test_gen_salt2(self):
        assert len(gen_salt(5)) == 5
        assert len(gen_salt(10)) == 10
        assert len(gen_salt(15)) == 15

    def test_gen_pwhash(self):
        res = gen_pwhash('foo')
        parts = res.split('$')

        assert parts[0] == 'sha1'
        assert len(parts[1]) == 10
        assert len(parts[2]) == 40

        res = gen_pwhash(u'bar')
        parts = res.split('$')

        assert parts[0] == 'sha1'
        assert len(parts[1]) == 10
        assert len(parts[2]) == 40

    def test_check_password(self):
        assert check_password('plain$$default', 'default') is True
        assert check_password('sha1$$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'password') is True
        assert check_password('sha1$$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'wrong') is False
        assert check_password('md5$xyz$bcc27016b4fdceb2bd1b369d5dc46c3f', u'example') is True
        assert check_password('sha1$5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'password') is False
        assert check_password('md42$xyz$bcc27016b4fdceb2bd1b369d5dc46c3f', 'example') is False

