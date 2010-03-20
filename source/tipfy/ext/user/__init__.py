# -*- coding: utf-8 -*-
"""
    tipfy.ext.user
    ~~~~~~~~~~~~~~

    User authentication and permissions extension.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime, timedelta

from google.appengine.api import users

from tipfy import cached_property, get_config, Forbidden, import_string, \
    local, redirect, RequestRedirect, url_for
from tipfy.ext.session import get_secure_cookie, set_secure_cookie

#: Default configuration values for this module. Keys are:
#:   - ``auth_system``: The default authentication class, as a string. Default
#:     is ``tipfy.ext.user.AppEngineAuth`` (uses App Engine's built in users
#:     system to login). To use own authentication or authentication with
#:     OpenId, OAuth, Google Accounts, Twitter, FriendFeed or Facebook (one,
#:     all or a mix of these), set it to ``tipfy.ext.user.MultiAuth``.
#:   - ``user_model``: A subclass of ``db.Model`` used for authenticated users,.
#:     as a string. Default is ``tipfy.ext.user.model:User``.
#:   - ``cookie_max_age``: Time in seconds before the authentication cookie
#:     data is invalidated. Both persistent and non-persitent authentications
#:     are affected by this setting - the difference is that non-persitent
#:     authentication only lasts for the current browser session. Default is 1
#:     week.
#:   - ``cookie_key``: Name of the autentication cookie. Default is
#:     'tipfy.ext.user'
#:   - ``cookie_domain``: Domain of the cookie. To work accross subdomains the
#:     domain must be set to the main domain with a preceding dot, e.g., cookies
#:     set for `.mydomain.org` will work in `foo.mydomain.org` and
#:     `bar.mydomain.org`. Default is ``None``, which means that cookies will
#:     only work for the current subdomain.
#:   - ``cookie_path``: Path in which the authentication cookie is valid.
#:     Default is `/`.
#:   - ``cookie_secure``: Make the cookie only available via HTTPS.
#:   - ``cookie_httponly``: Disallow JavaScript to access the cookie.
#:   - ``session_max_age``: Max age in seconds for a cookie session id. After
#:     that it is automatically renewed. Default is 1 week.
default_config = {
    'auth_system': None,
    'user_model': 'tipfy.ext.user.model:User',
    'cookie_max_age': 86400 * 7,
    'cookie_key': 'tipfy.ext.user',
    'cookie_domain': None,
    'cookie_path': '/',
    'cookie_secure': None,
    'cookie_httponly': False,
    'session_max_age': 86400 * 7,
}

#: Configured authentication system instance, cached in the module.
_auth_system = None
# Let other modules initialize user.
_is_ext_set = False


class UserMiddleware(object):
    """:class:`tipfy.RequestHandler` middleware that loads and persists a
    an user.
    """
    def pre_dispatch(self, handler):
        """Starts user session and adds user variables to context.

        :param handler:
            The current :class:`tipfy.RequestHandler` instance.
        """
        # Start user session.
        get_auth_system().login_with_session()

        # Set template variables.
        current_url = local.request.url
        current_user = get_current_user()
        is_logged_in = is_authenticated()

        handler.context.update({
            'current_user': current_user,
            'is_authenticated': is_logged_in,
        })

        if current_user is not None or is_logged_in is True:
            handler.context['logout_url'] = create_logout_url(current_url)
        else:
            handler.context['login_url'] = create_login_url(current_url)

        setattr(handler, 'current_user', current_user)

    def post_dispatch(self, handler, response):
        """Persists current user session, if needed.

        :param handler:
            The current :class:`tipfy.RequestHandler` instance.
        :param response:
            The current ``werkzeug.Response`` instance.
        """
        get_auth_system().save_session(response)


def setup(app):
    """Setup this extension.

    This will authenticate users and load the related
    :class:`tipfy.ext.user.model.User` entity from datastore. It will ask
    users to create an account if they are not created yet.

    To enable it, add this module to the list of extensions in ``config.py``:

    .. code-block:: python

       config = {
           'tipfy': {
               'extensions': [
                   'tipfy.ext.user',
                   # ...
               ],
           },
       }

    :param app:
        The WSGI application instance.
    :return:
        ``None``.
    """
    global _is_ext_set

    if _is_ext_set is False:
        # Setup configured authentication system.
        get_auth_system().setup(app)
        _is_ext_set = True


class BaseAuth(object):
    """Base authentication adapter."""
    #: Endpoint to the handler that creates a new user account.
    signup_endpoint = 'users/signup'

    #: Endpoint to the handler that logs in the user.
    login_endpoint = 'users/login'

    #: Endpoint to the handler that logs out the user.
    logout_endpoint = 'users/logout'

    @cached_property
    def user_model(self):
        """Returns the configured user model.

        :return:
            A :class:`tipfy.ext.user.model.User` class.
        """
        return import_string(get_config(__name__, 'user_model'))

    def setup(self, app):
        """Sets up this auth adapter. This is called when the user extension is
        installed.

        :param app:
            The WSGI Application instance.
        :return:
            ``None``.
        """

    def login_with_session(self, app, request):
        """Authenticates the current user using sessions.

        :return:
            ``None``.
        """
        local.user = None
        local.user_session = None

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
        local.user_session = None
        return False

    def login_with_external_data(self, data, remember=False):
        """Authenticates using data provided by an external service, such as
        OpenId, OAuth (Google Account, Twitter, Friendfeed) or Facebook.

        :return:
            ``None``.
        """
        local.user = None
        local.user_session = None

    def logout(self):
        """Logs out the current user.

        :return:
            ``None``.
        """
        local.user = None
        local.user_session = None

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
            return local.user.is_admin()

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
            :class:`tipfy.ext.user.model.User`.
        :return:
            The new :class:`tipfy.ext.user.model.User` entity, or ``None`` if
            the username already exists.
        """
        res = self.user_model.create(username, auth_id, **kwargs)

        if res and getattr(local, 'user_session', None) and \
            local.user_session.get('to_signup'):
            # Remove temporary data.
            del local.user_session['to_signup']

        return res


class MultiAuth(BaseAuth):
    """Authentication using own users or third party services such as OpenId,
    OAuth (Google, Twitter, FriendFeed) and Facebook.
    """
    @cached_property
    def cookie_args(self):
        """Returns the configured arguments to set an auth cookie.

        :return:
            A dictionary of keyword arguments for a cookie.
        """
        keys = ['key', 'domain', 'path', 'secure', 'httponly']
        return dict((k, get_config(__name__, 'cookie_' + k)) for k in keys)

    def setup(self, app):
        app.hooks.add('pre_dispatch_handler', self.login_with_session)
        app.hooks.add('post_dispatch_handler', self.save_session)

    def login_with_session(self):
        local.user = None
        local.user_session = None

        # Get the current session.
        session = get_secure_cookie(key=get_config(__name__, 'cookie_key'))

        # Check if we are in the middle of external auth and account creation.
        if session.get('to_signup'):
            # Redirect to account creation page.
            if not _is_auth_endpoint('signup_endpoint'):
                raise RequestRedirect(create_signup_url(request.url))

            local.user_session = session
            return

        # Get the authentication and session ids.
        auth_id = session.get('id', None)
        session_id = session.get('session_id', None)

        if auth_id is not None:
            user = self.user_model.get_by_auth_id(auth_id)
            if user is not None and user.check_session(session_id) is True:
                # Reset session id in case it was renewed by the model.
                session['session_id'] = user.session_id

                local.user = user
                local.user_session = session

    def login_with_form(self, username, password, remember=False):
        user = self.user_model.get_by_username(username)
        if user is not None and user.check_password(password) is True:
            local.user = user
            local.user_session = get_secure_cookie(data={
                'id': user.auth_id,
                'session_id': user.session_id,
                'remember': str(int(remember)),
            })
            res = True
        else:
            local.user = None
            local.user_session = None
            res = False

        return res

    def login_with_external_data(self, data, remember=False):
        local.user = None
        local.user_session = None

        auth_id = data.get('auth_id', None)
        if auth_id is None:
            return

        user = self.user_model.get_by_auth_id(auth_id)
        if user is not None:
            local.user = user
            local.user_session = get_secure_cookie(data={
                'id': user.auth_id,
                'session_id': user.session_id,
                'remember': str(int(remember)),
            })
        else:
            # Save temporary data while the user haven't created an account.
            local.user_session = get_secure_cookie(data={'to_signup': data})
            # Redirect to account creation page.
            if not _is_auth_endpoint('signup_endpoint'):
                raise RequestRedirect(create_signup_url(local.request.url))

    def logout(self):
        local.user = None
        if getattr(local, 'user_session', None) is not None:
            # Clear session and delete the cookie.
            local.user_session.clear()
            kwargs = self.cookie_args
            local.response.delete_cookie(kwargs['key'], path=kwargs['path'],
                domain=kwargs['domain'])
            local.user_session = None

    def save_session(self, response):
        """Pesists an authenticated user at the end of request.

        :param app:
            The current WSGI application.
        :param request:
            The current `werkzeug.Request` object.
        :param response:
            The current `werkzeug.Response` object.
        :return:
            ``None``.
        """
        if getattr(local, 'user_session', None) is not None:
            remember = local.user_session.get('remember', None)
            cookie_max_age = get_config(__name__, 'cookie_max_age')

            if remember == '1':
                # Persistent authentication.
                max_age = cookie_max_age
            else:
                # Non-persistent authentication (only lasts for a session).
                max_age = None

            session_expires = datetime.now() + timedelta(seconds=cookie_max_age)

            # Set the cookie on each request, resetting the idle countdown.
            set_secure_cookie(cookie=local.user_session,
                max_age=max_age,
                session_expires=session_expires,
                force=True,
                **self.cookie_args
            )


class AppEngineAuth(BaseAuth):
    """Authentication using App Engine's users module."""
    def setup(self, app):
        app.hooks.add('pre_dispatch_handler', self.login_with_session)

    def login_with_session(self, app, request):
        local.user = None
        local.user_session = None

        current_user = users.get_current_user()
        if current_user is None:
            return

        local.user = self.user_model.get_by_auth_id('gae|%s' %
            current_user.user_id())

        if local.user is None and not _is_auth_endpoint('signup_endpoint'):
            # User is logged in, but didn't create an account yet.
            raise RequestRedirect(create_signup_url(request.url))

    def create_login_url(self, dest_url):
        return users.create_login_url(dest_url)

    def create_logout_url(self, dest_url):
        return users.create_logout_url(dest_url)

    def is_authenticated(self):
        return (users.get_current_user() is not None)


def get_auth_system():
    """Returns the configured authentication system.

    :return:
        An instance of :class:`tipfy.ext.user.BaseAuth`.
    """
    global _auth_system
    if _auth_system is None:
        cls = get_config(__name__, 'auth_system', None)
        if cls is None:
            _auth_system = AppEngineAuth()
        else:
            _auth_system = import_string(cls)()

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
