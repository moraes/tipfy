# -*- coding: utf-8 -*-
"""
    Tests for tipfy.application
"""
import unittest

from nose.tools import raises

import _base

from google.appengine.api import users

from werkzeug import BaseResponse
from werkzeug.test import create_environ, Client

from gaetestbed import DataStoreTestCase

import tipfy
from tipfy import local
from tipfy.ext.auth import (AppEngineAuth, AuthMiddleware, BaseAuth,
    create_login_url, create_logout_url, create_signup_url, get_auth_system,
    get_current_user, is_current_user_admin, is_authenticated)
from tipfy.ext.auth.model import User


def get_url_map():
    return tipfy.Map([
        tipfy.Rule('/', endpoint='home', handler='files.app.handlers_auth.AuthHandler'),
        tipfy.Rule('/account/signup', endpoint='auth/signup', handler='files.app.handlers_auth.SignupHandler'),
        tipfy.Rule('/account/login', endpoint='auth/login', handler='undefined'),
        tipfy.Rule('/account/logout', endpoint='auth/logout', handler='undefined'),
    ])


def gae_login(user='me@mymail.com'):
    users.get_current_user = lambda user=user: users.User(user, _user_id=user) if user else None

def gae_logout():
    gae_login(None)


class TestAuthMiddlewareWithAppEngineAuth(DataStoreTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        app = tipfy.WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        app.url_adapter = app.url_map.bind('foo.com')

        self.temp_gcu = users.get_current_user

    def tearDown(self):
        tipfy.local_manager.cleanup()

        users.get_current_user = self.temp_gcu

    def test_pre_dispatch_no_user(self):
        app = tipfy.WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        app.url_adapter = app.url_map.bind('foo.com')

        gae_login(None)
        client = Client(app, response_wrapper=BaseResponse)

        response = client.open(path='/')
        # User is not logged in, so the page will be displayed normally.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Hello, World!')

    def test_pre_dispatch_user_without_account(self):
        app = tipfy.WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        app.url_adapter = app.url_map.bind('foo.com')

        gae_login()
        client = Client(app, response_wrapper=BaseResponse)

        response = client.open(path='/')
        # User is logged in, account doesn't exist: it will redirect to account creation.
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers['Location'], 'http://localhost/account/signup?redirect=http%3A%2F%2Flocalhost%2F')

    def test_pre_dispatch_user_with_account(self):
        app = tipfy.WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        app.url_adapter = app.url_map.bind('foo.com')

        gae_login()
        auth_id = 'gae|%s' % users.get_current_user().user_id()

        current_user = User.create('my_username', auth_id)
        assert isinstance(current_user, User)
        assert current_user == User.get_by_auth_id(auth_id)

        gae_login()

        middleware = AuthMiddleware()
        middleware.pre_dispatch(None)

        self.assertEqual(current_user, get_current_user())


class TestBaseAuth(unittest.TestCase):
    def setUp(self):
        app = tipfy.WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        app.url_adapter = app.url_map.bind('foo.com')

    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_user_model(self):
        auth = BaseAuth()
        assert auth.user_model is User

    def test_login_with_session(self):
        not_set = object()
        assert getattr(local, 'user', not_set) is not_set

        auth = BaseAuth()
        auth.login_with_session()

        assert local.user is None

    def test_login_with_form(self):
        not_set = object()
        assert getattr(local, 'user', not_set) is not_set

        auth = BaseAuth()
        res = auth.login_with_form('foo', 'bar', False)

        assert res is False
        assert local.user is None

    def test_login_with_external_data(self):
        not_set = object()
        assert getattr(local, 'user', not_set) is not_set

        auth = BaseAuth()
        auth.login_with_external_data('foo', False)

        assert local.user is None

    def test_logout(self):
        not_set = object()
        assert getattr(local, 'user', not_set) is not_set

        auth = BaseAuth()
        auth.logout()

        assert local.user is None

    def test_get_current_user(self):
        auth = BaseAuth()
        res = auth.get_current_user()
        assert res is None

    def test_is_current_user_admin(self):
        auth = BaseAuth()
        res = auth.is_current_user_admin()
        assert res is False

    def test_create_signup_url(self):
        auth = BaseAuth()

        res = auth.create_signup_url('/')
        assert res == 'http://foo.com/account/signup?redirect=%2F'

    def test_create_login_url(self):
        auth = BaseAuth()

        res = auth.create_login_url('/')
        assert res == 'http://foo.com/account/login?redirect=%2F'

    def test_create_logout_url(self):
        auth = BaseAuth()

        res = auth.create_logout_url('/')
        assert res == 'http://foo.com/account/logout?redirect=%2F'

    def test_is_authenticated(self):
        auth = BaseAuth()
        res = auth.is_authenticated()
        assert res is False


class TestMiscelaneous(unittest.TestCase):
    def setUp(self):
        app = tipfy.WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        app.url_adapter = app.url_map.bind('foo.com')

        import os
        os.environ['SERVER_NAME'] = 'foo.com'
        os.environ['USER_EMAIL'] = 'calvin@yukon.com'
        os.environ['SERVER_PORT'] = '8080'

    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_create_signup_url(self):
        res = create_signup_url('/')
        assert res == 'http://foo.com/account/signup?redirect=%2F'

    def test_create_login_url(self):
        res = create_login_url('/')
        assert res == '/_ah/login?continue=http%3A//foo.com%3A8080/'

    def test_create_logout_url(self):
        res = create_logout_url('/')
        assert res == '/_ah/login?continue=http%3A//foo.com%3A8080/&action=Logout'

    def test_get_auth_system(self):
        res = get_auth_system()
        assert isinstance(res, AppEngineAuth)

    def test_get_current_user(self):
        res = get_current_user()
        assert res is None

    def test_is_current_user_admin(self):
        res = is_current_user_admin()
        assert res is False

    def test_is_authenticated(self):
        res = is_authenticated()
        assert res is True
