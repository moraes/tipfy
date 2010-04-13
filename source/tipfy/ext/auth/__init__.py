# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth
    ~~~~~~~~~~~~~~

    User authentication and permissions extension.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime, timedelta

from google.appengine.api import users

from tipfy import (cached_property, get_config, Forbidden, import_string,
    local, redirect, RequestRedirect, url_for)
from tipfy.ext import session

#: Default configuration values for this module. Keys are:
#:
#: - ``auth_system``: The default authentication class, as a string. Default
#:   is ``tipfy.ext.auth.AppEngineAuth`` (uses App Engine's built in users
#:   system to login). To use own authentication or authentication with
#:   OpenId, OAuth, Google Accounts, Twitter, FriendFeed or Facebook (one,
#:   all or a mix of these), set it to ``tipfy.ext.auth.MultiAuth``.
#:
#: - ``user_model``: A subclass of ``db.Model`` used for authenticated users,.
#:   as a string. Default is ``tipfy.ext.auth.model:User``.
#:
#: - ``cookie_key``: Name of the autentication cookie. Default is
#:   'tipfy.ext.auth'
#:
#: - ``cookie_session_expires``: Session expiration time in seconds. Limits the
#:   duration of the contents of a cookie, even if a session cookie exists.
#:   If ``None``, the contents lasts as long as the cookie is valid. Default is
#:   ``None``.
#:
#: - ``cookie_max_age``: Time in seconds before the authentication cookie
#:   data is invalidated. Both persistent and non-persitent authentications
#:   are affected by this setting - the difference is that non-persitent
#:   authentication only lasts for the current browser session. Default is 1
#:   week.
#:
#: - ``cookie_domain``: Domain of the cookie. To work accross subdomains the
#:   domain must be set to the main domain with a preceding dot, e.g., cookies
#:   set for `.mydomain.org` will work in `foo.mydomain.org` and
#:   `bar.mydomain.org`. Default is ``None``, which means that cookies will
#:   only work for the current subdomain.
#:
#: - ``cookie_path``: Path in which the authentication cookie is valid.
#:   Default is `/`.
#:
#: - ``cookie_secure``: Make the cookie only available via HTTPS.
#:
#: - ``cookie_httponly``: Disallow JavaScript to access the cookie.
#:
#: - ``session_id_max_age``: Interval in seconds before an user session id is
#:   renewed. Default is 1 week.
default_config = {
    'auth_system': 'tipfy.ext.auth.AppEngineAuth',
    'user_model': 'tipfy.ext.auth.model.User',
    'cookie_key': 'tipfy.user',
    'cookie_session_expires': None,
    'cookie_max_age': 86400 * 7,
    'cookie_domain':   None,
    'cookie_path':     '/',
    'cookie_secure':   None,
    'cookie_httponly': False,
    'session_id_max_age': 86400 * 7,
}

#: Configured authentication system instance, cached in the module.
_auth_system = None


class AuthMiddleware(object):
    """:class:`tipfy.RequestHandler` middleware that loads and persists a
    an user.
    """
    def pre_dispatch(self, handler):
        """Executes before a :class:`tipfy.RequestHandler` is dispatched. If
        it returns a response object, it will stop the pre_dispatch middleware
        chain and won't run the requested handler method, using the returned
        response instead. However, post_dispatch hooks will still be executed.

        :param handler:
            A :class:`tipfy.RequestHandler` instance.
        :return:
            A ``werkzeug.Response`` instance or None.
        """
        # Start user session.
        get_auth_system().login_with_session()

    def pre_dispatch_handler(self):
        """Called if auth is used as a WSGIApplication middleware."""
        get_auth_system().login_with_session()
        return None


class BaseAuth(object):
    """Base authentication adapter."""
    #: Endpoint to the handler that creates a new user account.
    signup_endpoint = 'auth/signup'

    #: Endpoint to the handler that logs in the user.
    login_endpoint = 'auth/login'

    #: Endpoint to the handler that logs out the user.
    logout_endpoint = 'auth/logout'

    @cached_property
    def user_model(self):
        """Returns the configured user model.

        :return:
            A :class:`tipfy.ext.auth.model.User` class.
        """
        return import_string(get_config(__name__, 'user_model'))

    def login_with_session(self):
        """Authenticates the current user using sessions.

        :return:
            ``None``.
        """
        local.user = None

    def login_with_form(self, username, password, remember=False):
        """Authenticates the current user using data from a form.

        :param username:
            Username.
        :param password:
            Password.
        :param remember:
            True if authentication should be persisted even if user leaves the
            current session (the "remember me" feature).
        :return:
            ``True`` if login was succesfull, ``False`` otherwise.
        """
        local.user = None
        return False

    def login_with_external_data(self, data, remember=False):
        """Authenticates using data provided by an external service, such as
        OpenId, OAuth (Google Account, Twitter, Friendfeed) or Facebook.

        :return:
            ``None``.
        """
        local.user = None

    def logout(self):
        """Logs out the current user.

        :return:
            ``None``.
        """
        local.user = None

    def get_current_user(self):
        """Returns the currently logged in user entity or ``None``.

        :return:
            A :class:`User` entity, if the user for the current request is
            logged in, or ``None``.
        """
        return getattr(local, 'user', None)

    def is_current_user_admin(self):
        """Returns ``True`` if the current user is an admin.

        :return:
            ``True`` if the user for the current request is an admin, ``False``
            otherwise.
        """
        if getattr(local, 'user', None) is not None:
            return local.user.is_admin

        return False

    def create_signup_url(self, dest_url):
        """Returns the signup URL for this request and specified destination
        URL. By default returns the URL for the endpoint
        :attr:`signup_endpoint`.

        :param dest_url:
            String that is the desired final destination URL for the user once
            signup is complete.
        :return:
            An URL to perform signup.
        """
        return url_for(self.signup_endpoint, redirect=dest_url, full=True)

    def create_login_url(self, dest_url):
        """Returns the login URL for this request and specified destination URL.
         By default returns the URL for the endpoint :attr:`login_endpoint`.

        :param dest_url:
            String that is the desired final destination URL for the user once
            login is complete.
        :return:
            An URL to perform login.
        """
        return url_for(self.login_endpoint, redirect=dest_url, full=True)

    def create_logout_url(self, dest_url):
        """Returns the logout URL for this request and specified destination
        URL. By default returns the URL for the endpoint
        :attr:`logout_endpoint`.

        :param dest_url:
            String that is the desired final destination URL for the user once
            logout is complete.
        :return:
            An URL to perform logout.
        """
        return url_for(self.logout_endpoint, redirect=dest_url, full=True)

    def is_authenticated(self):
        """Returns ``True`` if the current user is logged in.

        :return:
            ``True`` if the user for the current request is authenticated,
            ``False`` otherwise.
        """
        # This is not really true but it is our best bet since 3rd party auth
        # is handled elsewhere.
        return (getattr(local, 'user', None) is not None)

    def create_user(self, username, auth_id, **kwargs):
        """Saves a new user in the datastore for the currently logged in user,
        and returns it. If the username already exists, returns ``None``.

        :param username:
            The unique username for this user.
        :param kwargs:
            Extra keyword arguments accepted by
            :class:`tipfy.ext.auth.model.User`.
        :return:
            The new :class:`tipfy.ext.auth.model.User` entity, or ``None`` if
            the username already exists.
        """
        return self.user_model.create(username, auth_id, **kwargs)


class MultiAuth(BaseAuth):
    """Authentication using own users or third party services such as OpenId,
    OAuth (Google, Twitter, FriendFeed) and Facebook.
    """
    @cached_property
    def cookie_key(self):
        return get_config(__name__, 'cookie_key')

    @cached_property
    def cookie_args(self):
        """Returns the configured arguments to set an auth cookie.

        :return:
            A dictionary of keyword arguments for a cookie.
        """
        keys = ['domain', 'path', 'secure', 'httponly', 'session_expires',
            'max_age']
        return dict((k, get_config(__name__, 'cookie_' + k)) for k in keys)

    def login_with_session(self):
        local.user = None

        # Check if a secure cookie is set.
        session = local.session_store.load_secure_cookie(self.cookie_key)

        if session.new is True:
            # Session didn't exist.
            return

        # Check if we are in the middle of external auth and account creation.
        if session.get('to_signup', None):
            # Redirect to account creation page.
            if not _is_auth_endpoint('signup_endpoint'):
                raise RequestRedirect(create_signup_url(local.request.url))

            return

        # Get the authentication and session ids.
        auth_id = session.get('id', None)
        session_id = session.get('session_id', None)
        remember = session.get('remember', '0')

        if auth_id is not None:
            user = self.user_model.get_by_auth_id(auth_id)
            if user is not None and user.check_session(session_id) is True:
                # Successful login. Make the user available.
                local.user = user
                # Add session to be saved at the end of request.
                # Reset session id in case it was renewed by the model.
                self.set_session(session, id=auth_id,
                    session_id=user.session_id, remember=remember)

    def login_with_form(self, username, password, remember=False):
        local.user = None
        user = self.user_model.get_by_username(username)

        if user is not None and user.check_password(password) is True:
            # Successful login. Make the user available.
            local.user = user
            # Store the cookie.
            self.set_session(id=user.auth_id, session_id=user.session_id,
                remember=str(int(remember)))
            return True

        # Authentication failed.
        return False

    def login_with_external_data(self, data, remember=False):
        local.user = None

        auth_id = data.get('auth_id', None)
        if auth_id is None:
            return

        user = self.user_model.get_by_auth_id(auth_id)

        if user is not None:
            local.user = user
            # Store the cookie.
            self.set_session(id=user.auth_id, session_id=user.session_id,
                remember=str(int(remember)))
        else:
            # Save temporary data while the user haven't created an account.
            self.set_session(to_signup=data)

            # Redirect to account creation page.
            # TODO: document this redirect.
            if not _is_auth_endpoint('signup_endpoint'):
                raise RequestRedirect(create_signup_url(local.request.url))

    def logout(self):
        local.user = None
        # Delete the cookie.
        local.session_store.set_cookie(self.cookie_key, None,
            **self.cookie_args)

    def set_session(self, session=None, **kwargs):
        """Renews the auth session."""
        if session:
            session.clear()
        else:
            session = local.session_store.create_secure_cookie()

        session.update(kwargs)

        # TODO add kwargs.
        cookie_args = dict(self.cookie_args)

        if kwargs.get('remember', '0') == '0':
            # Non-persistent authentication (only lasts for a session).
            cookie_args['max_age'] = None

        local.session_store.set_cookie(self.cookie_key, session, **cookie_args)

    def create_user(self, username, auth_id, **kwargs):
        user = self.user_model.create(username, auth_id, **kwargs)
        if user:
            self.set_session(id=user.auth_id, session_id=user.session_id,
                remember=0)

        return user


class AppEngineAuth(BaseAuth):
    """Authentication using App Engine's users module."""
    def login_with_session(self):
        local.user = None

        current_user = users.get_current_user()
        if current_user is None:
            return

        local.user = self.user_model.get_by_auth_id('gae|%s' %
            current_user.user_id())

        if local.user is None and not _is_auth_endpoint('signup_endpoint'):
            # User is logged in, but didn't create an account yet.
            raise RequestRedirect(create_signup_url(local.request.url))

    def create_login_url(self, dest_url):
        return users.create_login_url(dest_url)

    def create_logout_url(self, dest_url):
        return users.create_logout_url(dest_url)

    def is_authenticated(self):
        return (users.get_current_user() is not None)


def get_auth_system():
    """Returns the configured authentication system.

    :return:
        An instance of :class:`tipfy.ext.auth.BaseAuth`.
    """
    global _auth_system
    if _auth_system is None:
        _auth_system = import_string(get_config(__name__, 'auth_system'))()

    return _auth_system


def create_signup_url(dest_url):
    """Returns a URL that, when visited, prompts the user to sign up.

    Args:
        dest_url: str: A full URL or relative path to redirect to after signing
        up.
    Returns:
        str: A URL to perform sign up.
    """
    return get_auth_system().create_signup_url(dest_url)


def create_login_url(dest_url):
    """Returns a URL that, when visited, prompts the user to sign in.

    Args:
        dest_url: str: A full URL or relative path to redirect to after logging
        in.
    Returns:
        str: A URL to perform login.
    """
    return get_auth_system().create_login_url(dest_url)


def create_logout_url(dest_url):
    """Returns a URL that, when visited, logs out the user.

    Args:
        dest_url: str: A full URL or relative path to redirect to after logging
        out.
    Returns:
        str: A URL to perform logout.
    """
    return get_auth_system().create_logout_url(dest_url)


def get_current_user():
    """Returns an :class:`User` entity for the the currently logged in user or
    ``None``.

    :return:
        An :class:`User` entity if the user for the current request is logged
        in, or ``None``.
    """
    return get_auth_system().get_current_user()


def is_current_user_admin():
    """Returns ``True`` if the current user is an admin.

    :return:
        ``True`` if the user for the current request is an admin, ``False``
        otherwise.
    """
    return get_auth_system().is_current_user_admin()


def is_authenticated():
    """Returns ``True`` if the user is logged in. It is possible that an user
    is logged in and :func:`get_current_user()` is None if the user is
    authenticated but still haven't created an account.

    :return:
        ``True`` if the user for the current request is an logged in, ``False``
        otherwise.
    """
    return get_auth_system().is_authenticated()


def login_required(func):
    """A handler decorator to require user authentication. Normally
    :func:`user_required` is used instead.

    :param func:
        The handler method to be decorated.
    :return:
        The decorated method.
    """
    def decorated(*args, **kwargs):
        if is_authenticated() or _is_auth_endpoint('login_endpoint'):
            return func(*args, **kwargs)

        # Redirect to login page.
        return redirect(create_login_url(local.request.url))

    return decorated


def user_required(func):
    """A handler decorator to require the current user to be authenticated and
    to have an account saved in datastore.

    :param func:
        The handler method to be decorated.
    :return:
        The decorated method.
    """
    def decorated(*args, **kwargs):
        if get_current_user() or _is_auth_endpoint(('signup_endpoint',
            'login_endpoint')):
            return func(*args, **kwargs)

        if is_authenticated():
            # Redirect to signup page.
            return redirect(create_signup_url(local.request.url))
        else:
            # Redirect to login page.
            return redirect(create_login_url(local.request.url))

    return decorated


def admin_required(func):
    """A handler decorator to require the current user to be admin.

    :param func:
        The handler method to be decorated.
    :return:
        The decorated method.
    """
    def decorated(*args, **kwargs):
        if is_current_user_admin() or _is_auth_endpoint('login_endpoint'):
            return func(*args, **kwargs)

        if not is_authenticated():
            # Redirect to signup page.
            return redirect(create_login_url(local.request.url))

        # Nope, user isn't an admin.
        raise Forbidden()

    return decorated


def basic_auth_required(validator):
    """A decorator to authenticate using HTTP basic/digest authorization.
    This only wraps a handler method by a validator function.

    :param validator:
        A validator function that accepts a
        `werkzeug.datastructures.Authorization` to validate the request, plus
        the wrapped handler method and arguments.
    :return:
        The decorated method.
    """
    def wrapper(func):
        def decorated(*args, **kwargs):
            return validator(local.request.authorization, func, *args, **kwargs)

        return decorated

    return wrapper


def _is_auth_endpoint(endpoints):
    """Helper function to check if the current url is the given auth endpoint.

    :endpoint:
        An endpoint name, as a string, or a tuple of endpoint names.
    :return:
        ``True`` if the current url is the given auth endpoint.
    """
    if isinstance(endpoints, basestring):
        endpoints = (endpoints,)

    auth_system = get_auth_system()
    for e in endpoints:
        if local.app.rule.endpoint == getattr(auth_system, e, None):
            return True

    return False
