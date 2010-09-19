# -*- coding: utf-8 -*-
"""
    tipfy.auth
    ~~~~~~~~~~

    Base classes for user authentication.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import absolute_import

from google.appengine.api import users

from tipfy import abort

from werkzeug import cached_property, import_string
from werkzeug.routing import RequestRedirect

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


class BaseAuth(object):
    def __init__(self, app, request):
        self.app = app
        self.request = request
        self.secure_urls = app.get_config(__name__, 'secure_urls')

    @cached_property
    def user_model(self):
        """Returns the configured user model.

        :returns:
            A :class:`webapp2.ext.auth.model.User` class.
        """
        registry = self.app.registry
        key = 'ext.auth.user_model'
        if key not in registry:
            registry[key] = import_string(self.app.get_config(__name__,
                'user_model'))

        return registry[key]

    def _url(self, _name, **kwargs):
        kwargs.setdefault('redirect', self.request.path)
        if not self.app.debug and self.secure_urls:
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
    def user(self):
        raise NotImplementedError()

    @property
    def is_admin(self):
        return False

    @classmethod
    def factory(cls, _app, _name, **kwargs):
        if _name not in _app.request.registry:
            _app.request.registry[_name] = cls(_app, _app.request, **kwargs)

        return _app.request.registry[_name]


class AppEngineAuth(BaseAuth):
    """This RequestHandler mixin uses App Engine's built-in Users API. Main
    reasons to use it instead of Users API are:

    - You can use the decorator :func:`user_required` to require a user record
      stored in datastore after a user signs in.
    - It also adds a convenient access to current logged in user directly
      inside the handler, as well as the functions to generate auth-related
      URLs.
    - It standardizes how you create login, logout and signup URLs, and how
      you check for a logged in user and load an {{{User}}} entity. If you
      change to a different auth method later, these don't need to be
      changed in your code.
    """
    @cached_property
    def session(self):
        """Returns the currently logged in user session. For app Engine auth,
        this corresponds to the `google.appengine.api.users.User` object.

        :returns:
            A `google.appengine.api.users.User` object if the user for the
            current request is logged in, or None.
        """
        return users.get_current_user()

    @cached_property
    def user(self):
        """Returns the currently logged in user entity or None.

        :returns:
            A :class:`User` entity, if the user for the current request is
            logged in, or None.
        """
        if not self.session:
            return None

        auth_id = 'gae|%s' % self.session.user_id()
        return self.get_user_entity(auth_id=auth_id)

    @cached_property
    def is_admin(self):
        """Returns True if the current user is an admin.

        :returns:
            True if the user for the current request is an admin,
            False otherwise.
        """
        return users.is_current_user_admin()


class AppEngineMixedAuth(BaseAuth):
    @cached_property
    def session(self):
        """Returns the currently logged in user session."""
        # First try to get a user from the session.
        session_store = self.request.session_store
        cookie_name = self.app.get_config(__name__, 'cookie_name')
        session = session_store.get_session(cookie_name)
        if not session.get('user_id'):
            # User not found. Get it from built-in Users API.
            user = users.get_current_user()
            if user:
                session.update(gae_user_to_dict(user))
                auth_id = 'gae|%s' % session.get('user_id')
                self.user = self.get_user_entity(auth_id=auth_id)
                if self.user:
                    session['session_id'] = self.user.session_id

        return session

    @cached_property
    def user(self):
        """Returns the currently logged in user entity or None.

        :returns:
            A :class:`User` entity, if the user for the current request is
            logged in, or None.
        """
        # Get the authentication and session ids.
        user_id = self.session.get('user_id', None)
        if user_id is None:
            return None

        # Load user entity.
        auth_id = 'gae|%s' % user_id
        user = self.get_user_entity(auth_id=auth_id)
        if user is None:
            return None

        # Check if session matches.
        session_id = self.session.get('session_id', None)
        if not session_id or user.check_session(session_id) is not True:
            return None

        self._set_session(user.session_id)
        return user

    def _set_session(self, session_id):
        session_store = self.request.session_store
        cookie_name = self.app.get_config(__name__, 'cookie_name')

        cookie_args = self.app.get_config('tipfy.sessions', 'cookie_args')
        cookie_args = cookie_args.copy()

        remember = self.session.get('remember', '0')
        if remember == '0':
            # Non-persistent authentication (only lasts for a session).
            cookie_args['max_age'] = None
        else:
            cookie_args['max_age'] = self.app.get_config(__name__,
                'session_max_age')

        self.session['session_id'] = session_id
        session_store.set_session(cookie_name, self.session, **cookie_args)

    def logout(self):
        """Logs out the current user. This deletes the authentication session.
        """
        self.session.clear()

    def create_user(self, username, auth_id, **kwargs):
        user = super(AppEngineMixedAuth, self).create_user(username, auth_id,
            **kwargs)
        if user:
            self.session['session_id'] = user.session_id

        return user


class LoginRequiredPlugin(object):
    """A RequestHandler plugin to require user authentication. This
    acts as a `login_required` decorator but for handler classes. Example:

    .. code-block:: python

       from webapp2 import RequestHandler
       from webapp2.ext.auth import AppEngineAuthMixin, LoginRequiredPlugin

       class MyHandler(RequestHandler, AppEngineAuthMixin):
           plugin = [LoginRequiredPlugin]

           def get(self, **kwargs):
               return 'Only logged in users can see this.'
    """
    def before_dispatch(self, handler):
        return _login_required(handler)


class UserRequiredPlugin(object):
    """A RequestHandler plugin decorator to require the current user to
    have an account saved in datastore. This acts as a `user_required`
    decorator but for handler classes. Example:

    .. code-block:: python

       from webapp2 import RequestHandler
       from webapp2.ext.auth import AppEngineAuthMixin, UserRequiredPlugin

       class MyHandler(RequestHandler, AppEngineAuthMixin):
           plugin = [UserRequiredPlugin]

           def get(self, **kwargs):
               return 'Only users can see this.'
    """
    def before_dispatch(self, handler):
        return _user_required(handler)


class AdminRequiredPlugin(object):
    """A RequestHandler plugin to require the current user to be admin.
    This acts as a `admin_required` decorator but for handler classes. Example:

    .. code-block:: python

       from webapp2 import RequestHandler
       from webapp2.ext.auth import AppEngineAuthMixin, AdminRequiredPlugin

       class MyHandler(RequestHandler, AppEngineAuthMixin):
           plugin = [AdminRequiredPlugin]

           def get(self, **kwargs):
               return 'Only admins can see this.'
    """
    def before_dispatch(self, handler):
        return _admin_required(handler)


def login_required(func):
    """A RequestHandler method decorator to require user authentication.
    Normally :func:`user_required` is used instead. Example:

    .. code-block:: python

       from webapp2 import RequestHandler
       from webapp2.ext.auth import AppEngineAuthMixin, login_required

       class MyHandler(RequestHandler, AppEngineAuthMixin):
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

       from webapp2 import RequestHandler
       from webapp2.ext.auth import AppEngineAuthMixin, user_required

       class MyHandler(RequestHandler, AppEngineAuthMixin):
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


def admin_required(func):
    """A RequestHandler method decorator to require the current user to be
    admin. Example:

    .. code-block:: python

       from webapp2 import RequestHandler
       from webapp2.ext.auth import AppEngineAuthMixin, admin_required

       class MyHandler(RequestHandler, AppEngineAuthMixin):
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


def gae_user_to_dict(user):
    return {
        'nickname':           user.nickname(),
        'email':              user.email(),
        'user_id':            user.user_id(),
        'federated_identity': user.federated_identity(),
        'federated_provider': user.federated_provider(),
    }


def _login_required(handler):
    """Implementation for login_required and LoginRequiredPlugin."""
    auth = handler.request.auth

    if not auth.session:
        return handler.redirect(auth.login_url())


def _user_required(handler):
    """Implementation for user_required and UserRequiredPlugin."""
    auth = handler.request.auth

    if not auth.session:
        return handler.redirect(auth.login_url())

    if not auth.user:
        return handler.redirect(auth.signup_url())


def _admin_required(handler):
    """Implementation for admin_required and AdminRequiredPlugin."""
    auth = handler.request.auth

    if not auth.session:
        return handler.redirect(auth.login_url())

    if not auth.is_admin:
        abort(403)
