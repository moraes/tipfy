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
        self.secure_urls = app.get_config(__name__, 'secure_urls')

    @cached_property
    def user_model(self):
        """Returns the configured user model.

        :returns:
            A :class:`tipfy.auth.model.User` class.
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

    @classmethod
    def factory(cls, _app, _name, **kwargs):
        if _name not in _app.request.registry:
            _app.request.registry[_name] = cls(_app, _app.request, **kwargs)

        return _app.request.registry[_name]


class AppEngineAuthStore(BaseAuthStore):
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

        return self.get_user_entity(auth_id='gae|%s' % self.session.user_id())


class AppEngineMixedAuthStore(BaseAuthStore):
    def __init__(self, *args, **kwargs):
        super(AppEngineMixedAuthStore, self).__init__(*args, **kwargs)
        self.loaded = False
        self._session = None
        self._user = None

    @cached_property
    def session(self):
        """Returns the currently logged in user session."""
        if self.loaded is False:
            self._load_session_and_user()

        return self._session

    @cached_property
    def user(self):
        """Returns the currently logged in user entity or None.

        :returns:
            A :class:`User` entity, if the user for the current request is
            logged in, or None.
        """
        if self.loaded is False:
            self._load_session_and_user()

        return self._user

    def create_user(self, username, auth_id, **kwargs):
        user = super(AppEngineMixedAuthStore, self).create_user(username,
            auth_id, **kwargs)

        if user:
            self._set_session(auth_id, user)

        return user

    def logout(self):
        """Logs out the current user. This deletes the authentication session.
        """
        self.loaded = True
        self._session_base.pop('_auth', None)
        self._user = None
        self._session = None

    @cached_property
    def _session_base(self):
        cookie_name = self.app.get_config(__name__, 'cookie_name')
        return self.request.session_store.get_session(cookie_name)

    def _set_session(self, auth_id, user=None):
        config = self.app.get_config(__name__)
        kwargs = self.app.get_config('tipfy.sessions', 'cookie_args').copy()
        kwargs['max_age'] = None

        session = {'id': auth_id}
        if user:
            session['token'] = user.session_id
            if user.auth_remember:
                kwargs['max_age'] = config.get('session_max_age')

        self._session_base['_auth'] = self._session = session
        self.request.session_store.set_session(config.get('cookie_name'),
            self._session_base, **kwargs)

    def _load_session_and_user(self):
        self.loaded = True
        session = self._session_base.get('_auth', {})
        gae_user = users.get_current_user()

        if gae_user:
            auth_id = 'gae|%s' % gae_user.user_id()
        else:
            auth_id = session.get('id')

        if auth_id is None:
            # No session, no user.
            return

        # Fetch the user entity.
        user = self.get_user_entity(auth_id=auth_id)
        if user is None:
            if gae_user:
                return self._set_session(auth_id)

            # Bad auth id, no fallback: must log in again.
            return self.logout()

        current_token = user.session_id
        if not user.check_session(session.get('token')):
            # Token didn't match.
            return self.logout()

        if (current_token != user.session_id) or user.auth_remember:
            # Token was updated or we need to renew session per request.
            self._set_session(auth_id, user)

        self._user = user


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


def gae_user_to_dict(user):
    return {
        'nickname':           user.nickname(),
        'email':              user.email(),
        'user_id':            user.user_id(),
        'federated_identity': user.federated_identity(),
        'federated_provider': user.federated_provider(),
    }


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
