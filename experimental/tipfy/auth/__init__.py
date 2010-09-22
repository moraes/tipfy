# -*- coding: utf-8 -*-
"""
    tipfy.auth
    ~~~~~~~~~~

    Base classes for user authentication.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import absolute_import

from tipfy import abort, APPENGINE

from werkzeug import cached_property, import_string

#: Default configuration values for this module. Keys are:
#:
#: user_model
#:     A ``db.Model`` class used for authenticated users, as a string.
#:     Default is `tipfy.auth.model.User`.
#:
#: secure_urls
#:     True to use secure URLs for login, logout and sign up, False otherwise.
#:     Default is False.
#:
#: cookie_name
#:     Name of the autentication cookie. Default is `auth`.
#:
#: session_max_age
#:     Interval in seconds before a user session id is renewed.
#:     Default is 1 week.
default_config = {
    'user_model':      'tipfy.auth.model.User',
    'cookie_name':     'auth',
    'secure_urls':     False,
    'session_max_age': 86400 * 7,
}


class BaseAuthStore(object):
    def __init__(self, app, request):
        self.app = app
        self.request = request
        self.config = app.get_config(__name__)

    @cached_property
    def user_model(self):
        """Returns the configured user model.

        :returns:
            A :class:`tipfy.auth.model.User` class.
        """
        registry = self.app.registry
        key = 'auth.user_model'
        if key not in registry:
            registry[key] = import_string(self.config.get('user_model'))

        return registry[key]

    @cached_property
    def _session_base(self):
        cookie_name = self.config.get('cookie_name')
        return self.request.session_store.get_session(cookie_name)

    def _url(self, _name, **kwargs):
        kwargs.setdefault('redirect', self.request.path)
        if not self.app.dev and self.config.get('secure_urls'):
            kwargs['_scheme'] = 'https'

        return self.app.url_for(_name, **kwargs)

    def login_url(self, **kwargs):
        """Returns a URL that, when visited, prompts the user to sign in.

        :returns:
            A URL to perform logout.
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
            A URL to perform logout.
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

    @classmethod
    def factory(cls, _app, _name, **kwargs):
        if _name not in _app.request.registry:
            _app.request.registry[_name] = cls(_app, _app.request, **kwargs)

        return _app.request.registry[_name]


class LoginRequiredMiddleware(object):
    """A RequestHandler middleware to require user authentication. This
    acts as a `login_required` decorator but for handler classes. Example:

    .. code-block:: python

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
    for handler classes. Example:

    .. code-block:: python

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
    Example:

    .. code-block:: python

       from tipfy import RequestHandler
       from tipfy.auth import UserRequiredIfAuthenticatedMiddleware

       class MyHandler(RequestHandler):
           middleware = [UserRequiredIfAuthenticatedMiddleware]

           def get(self, **kwargs):
               return 'Only non-logged in users or users with saved accounts can see this.'
    """
    def before_dispatch(self, handler):
        return _user_required_if_authenticated(handler)


class AdminRequiredMiddleware(object):
    """A RequestHandler middleware to require the current user to be admin.
    This acts as a `admin_required` decorator but for handler classes. Example:

    .. code-block:: python

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
    Normally :func:`user_required` is used instead. Example:

    .. code-block:: python

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
    have an account saved in datastore. Example:

    .. code-block:: python

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
    have an account saved in datastore, but only if he is logged in. Example:

    .. code-block:: python

       from tipfy import RequestHandler
       from tipfy.auth import user_required_if_authenticated

       class MyHandler(RequestHandler):
           @user_required_if_authenticated
           def get(self, **kwargs):
               return 'Only non-logged in users or users with saved accounts can see this.'

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
    admin. Example:

    .. code-block:: python

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


def _login_required(handler):
    """Implementation for login_required and LoginRequiredMiddleware."""
    auth = handler.request.auth

    if not auth.session:
        return handler.redirect(auth.login_url())


def _user_required(handler):
    """Implementation for user_required and UserRequiredMiddleware."""
    auth = handler.request.auth

    if not auth.session:
        return handler.redirect(auth.login_url())

    if not auth.user:
        return handler.redirect(auth.signup_url())


def _user_required_if_authenticated(handler):
    """Implementation for user_required_if_authenticated and
    UserRequiredIfAuthenticatedMiddleware.
    """
    auth = handler.request.auth

    if auth.session and not auth.user:
        return handler.redirect(auth.signup_url())


def _admin_required(handler):
    """Implementation for admin_required and AdminRequiredMiddleware."""
    auth = handler.request.auth

    if not auth.session:
        return handler.redirect(auth.login_url())

    if not auth.is_admin:
        abort(403)


if APPENGINE:
    from tipfy.auth.appengine import (AppEngineAuthStore,
        AppEngineMixedAuthStore)
