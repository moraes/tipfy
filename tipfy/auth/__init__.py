# -*- coding: utf-8 -*-
"""
    tipfy.auth
    ~~~~~~~~~~

    Base classes for user authentication.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import absolute_import

import uuid

from werkzeug import abort

from tipfy import DEV_APPSERVER

from werkzeug import (cached_property, check_password_hash,
    generate_password_hash, import_string)

#: Default configuration values for this module. Keys are:
#:
#: user_model
#:     A ``db.Model`` class used for authenticated users, as a string.
#:     Default is `tipfy.appengine.auth.model.User`.
#:
#: secure_urls
#:     True to use secure URLs for login, logout and sign up, False otherwise.
#:     Default is False.
#:
#: cookie_name
#:     Name of the autentication cookie. Default is `session`, which stores
#:     the data in the default session.
#:
#: session_max_age
#:     Interval in seconds before a user session id is renewed.
#:     Default is 1 week.
default_config = {
    'user_model':      'tipfy.appengine.auth.model.User',
    'cookie_name':     'session',
    'secure_urls':     False,
    'session_max_age': 86400 * 7,
}


class BaseAuthStore(object):
    def __init__(self, handler):
        self.handler = handler
        self.app = handler.app
        self.request = handler.request
        self.config = handler.app.config[__name__]

    @cached_property
    def user_model(self):
        """Returns the configured user model.

        :returns:
            A :class:`tipfy.auth.model.User` class.
        """
        registry = self.app.registry
        key = 'auth.user_model'
        if key not in registry:
            registry[key] = import_string(self.config['user_model'])

        return registry[key]

    @cached_property
    def _session_base(self):
        cookie_name = self.config['cookie_name']
        return self.handler.session_store.get_session(cookie_name)

    def _url(self, _name, **kwargs):
        kwargs.setdefault('redirect', self.request.path)
        if not DEV_APPSERVER and self.config['secure_urls']:
            kwargs['_scheme'] = 'https'

        return self.handler.url_for(_name, **kwargs)

    def login_url(self, **kwargs):
        """Returns a URL that, when visited, prompts the user to sign in.

        :returns:
            A URL to perform login.
        """
        return self._url('auth/login', **kwargs)

    def logout_url(self, **kwargs):
        """Returns a URL that, when visited, logs out the user.

        :returns:
            A URL to perform logout.
        """
        return self._url('auth/logout', **kwargs)

    def signup_url(self, **kwargs):
        """Returns a URL that, when visited, prompts the user to sign up.

        :returns:
            A URL to perform signup.
        """
        return self._url('auth/signup', **kwargs)

    def create_user(self, username, auth_id, **kwargs):
        """Creates a new user entity.

        :param username:
            Unique username.
        :param auth_id:
            Unique authentication id. For App Engine users it is 'gae:user_id'.
        :returns:
            The new entity if the username is available, None otherwise.
        """
        return self.user_model.create(username, auth_id, **kwargs)

    def get_user_entity(self, username=None, auth_id=None):
        """Loads an user entity from datastore. Override this to implement
        a different loading method. This method will load the user depending
        on the way the user is being authenticated: for form authentication,
        username is used; for third party or App Engine authentication,
        auth_id is used.

        :param username:
            Unique username.
        :param auth_id:
            Unique authentication id.
        :returns:
            A ``User`` model instance, or None.
        """
        if auth_id:
            return self.user_model.get_by_auth_id(auth_id)
        elif username:
            return self.user_model.get_by_username(username)

    @property
    def session(self):
        """The auth session. For third party auth, it is possible that an
        auth session exists but :attr:`user` is None (the user wasn't created
        yet). We access the session to check if the user is logged in but
        doesn't have an account.
        """
        raise NotImplementedError()

    @property
    def user(self):
        """The user entity."""
        raise NotImplementedError()


class SessionAuthStore(BaseAuthStore):
    """Base store for auth stores that use own session."""
    def __init__(self, *args, **kwargs):
        super(SessionAuthStore, self).__init__(*args, **kwargs)
        self.loaded = False
        self._session = self._user = None

    @property
    def session(self):
        """Returns the currently logged in user session."""
        if not self.loaded:
            self._load_session_and_user()

        return self._session

    @property
    def user(self):
        """Returns the currently logged in user entity or None.

        :returns:
            A :class:`User` entity, if the user for the current request is
            logged in, or None.
        """
        if not self.loaded:
            self._load_session_and_user()

        return self._user

    def create_user(self, username, auth_id, **kwargs):
        user = super(SessionAuthStore, self).create_user(username,
            auth_id, **kwargs)

        if user:
            self._set_session(auth_id, user)

        return user

    def logout(self):
        """Logs out the current user. This deletes the authentication session.
        """
        self.loaded = True
        self._session_base.pop('_auth', None)
        self._session = self._user = None

    def _load_session_and_user(self):
        raise NotImplementedError()

    def _set_session(self, auth_id, user=None, remember=False):
        kwargs = {}
        session = {'id': auth_id}
        if user:
            session['token'] = user.session_id

        if remember:
            kwargs['max_age'] = self.config['session_max_age']
        else:
            kwargs['max_age'] = None

        self._session_base['_auth'] = self._session = session
        self.handler.session_store.update_session_args(
            self.config['cookie_name'], **kwargs)


class MultiAuthStore(SessionAuthStore):
    """Store used for custom or third party authentication."""
    def login_with_form(self, username, password, remember=False):
        """Authenticates the current user using data from a form.

        :param username:
            Username.
        :param password:
            Password.
        :param remember:
            True if authentication should be persisted even if user leaves the
            current session (the "remember me" feature).
        :returns:
            True if login was succesfull, False otherwise.
        """
        self.loaded = True
        user = self.get_user_entity(username=username)

        if user is not None and user.check_password(password):
            # Successful login. Check if session id needs renewal.
            user.renew_session(max_age=self.config['session_max_age'])
            # Make the user available.
            self._user = user
            # Store the cookie.
            self._set_session(user.auth_id, user, remember)
            return True

        # Authentication failed.
        return False

    def login_with_auth_id(self, auth_id, remember=False, **kwargs):
        """Called to authenticate the user after a third party confirmed
        authentication.

        :param auth_id:
            Authentication id, generally a combination of service name and
            user identifier for the service, e.g.: 'twitter|john'.
        :param remember:
            True if authentication should be persisted even if user leaves the
            current session (the "remember me" feature).
        :returns:
            None. This always authenticates the user.
        """
        self.loaded = True
        self._user = self.get_user_entity(auth_id=auth_id)

        if self._user:
            # Set current user from datastore.
            self._set_session(auth_id, self._user, remember)
        else:
            # Simply set a session; user will be created later if required.
            self._set_session(auth_id, remember=remember)

    def _load_session_and_user(self):
        self.loaded = True
        session = self._session_base.get('_auth', {})
        auth_id = session.get('id')
        session_token = session.get('token')

        if auth_id is None or session_token is None:
            # No session, no user.
            return

        self._session = session

        # Fetch the user entity.
        user = self.get_user_entity(auth_id=auth_id)

        if user is None:
            # Bad auth id or token, no fallback: must log in again.
            return

        current_token = user.session_id
        if not user.check_session(session_token):
            # Token didn't match.
            return self.logout()

        # Successful login. Check if session id needs renewal.
        user.renew_session(max_age=self.config['session_max_age'])

        if (current_token != user.session_id) or user.auth_remember:
            # Token was updated or we need to renew session per request.
            self._set_session(auth_id, user, user.auth_remember)

        self._user = user


class LoginRequiredMiddleware(object):
    """A RequestHandler middleware to require user authentication. This
    acts as a `login_required` decorator but for handler classes. Example::

        from tipfy import RequestHandler
        from tipfy.auth import LoginRequiredMiddleware

        class MyHandler(RequestHandler):
            middleware = [LoginRequiredMiddleware]

            def get(self, **kwargs):
                return 'Only logged in users can see this.'
    """
    def before_dispatch(self, handler):
        return _login_required(handler)


class UserRequiredMiddleware(object):
    """A RequestHandler middleware to require the current user to have an
    account saved in datastore. This acts as a `user_required` decorator but
    for handler classes. Example::

        from tipfy import RequestHandler
        from tipfy.auth import UserRequiredMiddleware

        class MyHandler(RequestHandler):
            middleware = [UserRequiredMiddleware]

            def get(self, **kwargs):
                return 'Only users can see this.'
    """
    def before_dispatch(self, handler):
        return _user_required(handler)


class UserRequiredIfAuthenticatedMiddleware(object):
    """A RequestHandler middleware to require the current user to have an
    account saved in datastore, but only if he is logged in. This acts as a
    `user_required_if_authenticated` decorator but for handler classes.
    Example::

        from tipfy import RequestHandler
        from tipfy.auth import UserRequiredIfAuthenticatedMiddleware

        class MyHandler(RequestHandler):
            middleware = [UserRequiredIfAuthenticatedMiddleware]

            def get(self, **kwargs):
                return 'Only non-logged in users or users with saved '
                    'accounts can see this.'
    """
    def before_dispatch(self, handler):
        return _user_required_if_authenticated(handler)


class AdminRequiredMiddleware(object):
    """A RequestHandler middleware to require the current user to be admin.
    This acts as a `admin_required` decorator but for handler classes.
    Example::

        from tipfy import RequestHandler
        from tipfy.auth import AdminRequiredMiddleware

        class MyHandler(RequestHandler):
            middleware = [AdminRequiredMiddleware]

            def get(self, **kwargs):
                return 'Only admins can see this.'
    """
    def before_dispatch(self, handler):
        return _admin_required(handler)


def login_required(func):
    """A RequestHandler method decorator to require user authentication.
    Normally :func:`user_required` is used instead. Example::

        from tipfy import RequestHandler
        from tipfy.auth import login_required

        class MyHandler(RequestHandler):
            @login_required
            def get(self, **kwargs):
                return 'Only logged in users can see this.'

    :param func:
        The handler method to be decorated.
    :returns:
        The decorated method.
    """
    def decorated(self, *args, **kwargs):
        return _login_required(self) or func(self, *args, **kwargs)

    return decorated


def user_required(func):
    """A RequestHandler method decorator to require the current user to
    have an account saved in datastore. Example::

        from tipfy import RequestHandler
        from tipfy.auth import user_required

        class MyHandler(RequestHandler):
            @user_required
            def get(self, **kwargs):
                return 'Only users can see this.'

    :param func:
        The handler method to be decorated.
    :returns:
        The decorated method.
    """
    def decorated(self, *args, **kwargs):
        return _user_required(self) or func(self, *args, **kwargs)

    return decorated


def user_required_if_authenticated(func):
    """A RequestHandler method decorator to require the current user to
    have an account saved in datastore, but only if he is logged in. Example::

        from tipfy import RequestHandler
        from tipfy.auth import user_required_if_authenticated

        class MyHandler(RequestHandler):
            @user_required_if_authenticated
            def get(self, **kwargs):
                return 'Only non-logged in users or users with saved '
                    'accounts can see this.'

    :param func:
        The handler method to be decorated.
    :returns:
        The decorated method.
    """
    def decorated(self, *args, **kwargs):
        return _user_required_if_authenticated(self) or \
            func(self, *args, **kwargs)

    return decorated


def admin_required(func):
    """A RequestHandler method decorator to require the current user to be
    admin. Example::

        from tipfy import RequestHandler
        from tipfy.auth import admin_required

        class MyHandler(RequestHandler):
            @admin_required
            def get(self, **kwargs):
                return 'Only admins can see this.'

    :param func:
        The handler method to be decorated.
    :returns:
        The decorated method.
    """
    def decorated(self, *args, **kwargs):
        return _admin_required(self) or func(self, *args, **kwargs)

    return decorated


def create_session_id():
    return uuid.uuid4().hex


def _login_required(handler):
    """Implementation for login_required and LoginRequiredMiddleware."""
    auth = handler.auth

    if not auth.session:
        return handler.redirect(auth.login_url())


def _user_required(handler):
    """Implementation for user_required and UserRequiredMiddleware."""
    auth = handler.auth

    if not auth.session:
        return handler.redirect(auth.login_url())

    if not auth.user:
        return handler.redirect(auth.signup_url())


def _user_required_if_authenticated(handler):
    """Implementation for user_required_if_authenticated and
    UserRequiredIfAuthenticatedMiddleware.
    """
    auth = handler.auth

    if auth.session and not auth.user:
        return handler.redirect(auth.signup_url())


def _admin_required(handler):
    """Implementation for admin_required and AdminRequiredMiddleware."""
    auth = handler.auth

    if not auth.session:
        return handler.redirect(auth.login_url())

    if not auth.user or not auth.user.is_admin:
        abort(403)
