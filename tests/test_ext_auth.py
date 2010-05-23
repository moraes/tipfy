# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.auth
"""
import unittest

from nose.tools import raises

import _base

from google.appengine.api import users

from werkzeug import BaseResponse
from werkzeug.contrib.securecookie import SecureCookie
from werkzeug.test import create_environ, Client

from gaetestbed import DataStoreTestCase

from tipfy import abort, Forbidden, local, Map, Request, Rule, WSGIApplication
from tipfy.ext.auth import (AppEngineAuth, AuthMiddleware, BaseAuth,
    basic_auth_required,
    create_login_url, create_logout_url, create_signup_url, get_auth_system,
    get_current_user, is_current_user_admin, is_authenticated, MultiAuth,
    _auth_system)
from tipfy.ext.auth.model import User
from tipfy.ext.session import SessionMiddleware


def get_url_map():
    return Map([
        Rule('/', endpoint='home', handler='files.app.handlers_auth.AuthHandler'),
        Rule('/account/signup', endpoint='auth/signup', handler='files.app.handlers_auth.SignupHandler'),
        Rule('/account/login', endpoint='auth/login', handler='undefined'),
        Rule('/account/logout', endpoint='auth/logout', handler='undefined'),
    ])


def gae_login(user='me@mymail.com'):
    users.get_current_user = lambda user=user: users.User(user, _user_id=user) if user else None

def gae_logout():
    gae_login(None)


class TestAuthMiddlewareWithAppEngineAuth(DataStoreTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        app = WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        app.url_adapter = app.url_map.bind('foo.com')

        self.temp_gcu = users.get_current_user

    def tearDown(self):
        local.__release_local__()

        users.get_current_user = self.temp_gcu

    def test_pre_dispatch_no_user(self):
        app = WSGIApplication({'tipfy': {
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
        app = WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        #app.url_adapter = app.url_map.bind('foo.com')

        gae_login()
        client = Client(app, response_wrapper=BaseResponse)

        response = client.open(path='/')
        # User is logged in, account doesn't exist: it will redirect to account creation.
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers['Location'], 'http://localhost/account/signup?redirect=http%3A%2F%2Flocalhost%2F')

    def test_pre_dispatch_user_with_account(self):
        app = WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        app.url_adapter = app.url_map.bind('foo.com')

        gae_login()
        auth_id = 'gae|%s' % users.get_current_user().user_id()

        current_user = User.create('my_username', auth_id)
        assert isinstance(current_user, User)
        assert current_user == User.get_by_auth_id(auth_id)

        middleware = AuthMiddleware()
        middleware.pre_dispatch(None)

        self.assertEqual(current_user, get_current_user())

    def test_pre_dispatch_user_with_admin_account(self):
        app = WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        app.url_adapter = app.url_map.bind('foo.com')

        gae_login()
        auth_id = 'gae|%s' % users.get_current_user().user_id()

        current_user = User.create('my_username', auth_id, is_admin=True)
        assert isinstance(current_user, User)
        assert current_user == User.get_by_auth_id(auth_id)

        middleware = AuthMiddleware()
        middleware.pre_dispatch(None)

        self.assertEqual(is_current_user_admin(), True)


class TestBaseAuth(DataStoreTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        local.request = Request.from_values(base_url='http://foo.com')
        app = WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        app.match_url(local.request)

    def tearDown(self):
        local.__release_local__()

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

    def test_create_user_duplicate(self):
        auth = BaseAuth()
        user = auth.create_user('my_username', 'my_auth_id')
        assert user is not None

        user = auth.create_user('my_username', 'my_auth_id')
        assert user is None


class TestMultiAuth(unittest.TestCase):
    def setUp(self):
        app = WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        app.url_adapter = app.url_map.bind('foo.com')

    def tearDown(self):
        local.__release_local__()



class TestMiscelaneous(unittest.TestCase):
    def setUp(self):
        local.request = Request.from_values(base_url='http://foo.com')
        app = WSGIApplication({'tipfy': {
            'url_map': get_url_map(),
        }})
        app.match_url(local.request)

        import os
        os.environ['SERVER_NAME'] = 'foo.com'
        os.environ['USER_EMAIL'] = 'calvin@yukon.com'
        os.environ['SERVER_PORT'] = '8080'

    def tearDown(self):
        local.__release_local__()

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

    def test_basic_auth_required(self):
        local.request = Request.from_values(environ_base={
            'HTTP_AUTHORIZATION': 'BASIC %s' % 'foo:bar'.encode('base64'),
        })
        assert local.request.authorization is not None

        def validator(authorization, func, *args, **kwargs):
            if authorization is not None and \
                authorization.username == 'foo' and \
                authorization.password == 'bar':
                return func(*args, **kwargs)

            abort(403)

        def func():
            return 'I am authorized.'

        wrapper = basic_auth_required(validator)
        decorated = wrapper(func)
        assert decorated() == 'I am authorized.'

    @raises(Forbidden)
    def test_basic_auth_required_invalid_authorization(self):
        local.request = Request.from_values(environ_base={
            'HTTP_AUTHORIZATION': 'BASIC %s' % 'foo:baz'.encode('base64'),
        })
        assert local.request.authorization is not None

        def validator(authorization, func, *args, **kwargs):
            if authorization is not None and \
                authorization.username == 'foo' and \
                authorization.password == 'bar':
                return func(*args, **kwargs)

            abort(403)

        def func():
            return 'I am authorized.'

        wrapper = basic_auth_required(validator)
        decorated = wrapper(func)
        assert decorated() == 'I am authorized.'

    @raises(Forbidden)
    def test_basic_auth_required_no_authorization(self):
        local.request = Request.from_values()

        def validator(authorization, func, *args, **kwargs):
            if authorization is not None and \
                authorization.username == 'foo' and \
                authorization.password == 'bar':
                return func(*args, **kwargs)

            abort(403)

        def func():
            return 'I am authorized.'

        wrapper = basic_auth_required(validator)
        decorated = wrapper(func)
        assert decorated() == 'I am authorized.'
