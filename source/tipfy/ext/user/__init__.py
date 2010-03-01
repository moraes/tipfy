# -*- coding: utf-8 -*-
"""
    tipfy.ext.user
    ~~~~~~~~~~~~~~

    User authentication and permissions extension.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import import_string, get_config, app, request, redirect, \
    Forbidden

#: Default configuration values for this module. Keys are:
#:   - ``auth_system``: The default authentication class, as a string. Default
#:     is ``tipfy.ext.user.auth.google:GoogleAuth``.
#:   - ``user_model``: A subclass of ``db.Model`` used for authenticated users,.
#:     as a string. Default is ``tipfy.ext.user.models:User``.
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
#:     `bar.mydomain.org`. Default is `None`, which means that cookies will
#:     only work for the current subdomain.
#:   - ``cookie_path``: Path in which the authentication cookie is valid.
#:     Default is `/`.
#:   - ``cookie_secure``: Make the cookie only available via HTTPS.
#:   - ``cookie_httponly``: Disallow JavaScript to access the cookie.
default_config = {
    'auth_system': 'tipfy.ext.user.auth.google_account:GoogleAuth',
    'user_model':  'tipfy.ext.user.models:User',
    # Cookie settings
    'cookie_max_age': 86400 * 7,
    'cookie_key': 'tipfy.ext.user',
    'cookie_domain': None,
    'cookie_path': '/',
    'cookie_secure': None,
    'cookie_httponly': False,
}

#: Configured authentication system instance, cached in the module.
_auth_system = None
# Let other modules initialize user.
is_ext_set = False


def setup():
    """Setup this extension.

    This will authenticate users and load the related
    :class:`tipfy.ext.user.models.User` entity from datastore. It will ask
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

    :return:
        ``None``.
    """
    global is_ext_set
    if is_ext_set is False:
        auth_system = get_auth_system()

        # Setup specific auth stuff, if needed.
        auth_system.setup()

        # Add hook to load user on each request.
        app.hooks.add('pre_dispatch_handler', auth_system.login)

        is_ext_set = True


def get_auth_system():
    """Returns the configured authentication system.

    :return:
        An instance of :class:`tipfy.ext.user.auth.BaseAuth`.
    """
    global _auth_system
    if _auth_system is None:
        _auth_system = import_string(get_config(__name__, 'auth_system'))()

    return _auth_system


def create_signup_url(dest_url):
    """Returns the signup URL for this request and specified destination URL.

    :param dest_url:
        String that is the desired final destination URL for the user once
        signup is complete.
    :return:
        An URL to perform login.
    """
    return get_auth_system().create_signup_url(dest_url)


def create_login_url(dest_url):
    """Returns the login URL for this request and specified destination URL.

    :param dest_url:
        String that is the desired final destination URL for the user once
        login is complete.
    :return:
        An URL to perform login.
    """
    return get_auth_system().create_login_url(dest_url)


def create_logout_url(dest_url):
    """Returns the logout URL for this request and specified destination URL.

    :param dest_url:
        String that is the desired final destination URL for the user once
        logout is complete.
    :return:
        An URL to perform logout.
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


def is_logged_in():
    """Returns ``True`` if the user is logged in. It is possible that an user
    is logged in and :func:`get_current_user()` is None: it happens when the
    user authenticated but still didn't create an account.

    :return:
        ``True`` if the user for the current request is an admin, ``False``
        otherwise.
    """
    return get_auth_system().is_logged_in()


def login_required(func):
    """A handler decorator to require user authentication.

    :param func:
        The handler method to be decorated.
    :return:
        The decorated method.
    """
    def decorated(*args, **kwargs):
        if is_logged_in():
            return func(*args, **kwargs)

        # Redirect to login page.
        return redirect(create_login_url(request.url))

    return decorated


def user_required(func):
    """A handler decorator to require the current user to have an account.

    :param func:
        The handler method to be decorated.
    :return:
        The decorated method.
    """
    def decorated(*args, **kwargs):
        if get_current_user() is not None:
            return func(*args, **kwargs)

        if is_logged_in():
            # Redirect to signup page.
            return redirect(create_signup_url(request.url))

        # Redirect to login page.
        return redirect(create_login_url(request.url))

    return decorated


def admin_required(func):
    """A handler decorator to require the current user to be admin.

    :param func:
        The handler method to be decorated.
    :return:
        The decorated method.
    """
    def decorated(*args, **kwargs):
        if is_current_user_admin():
            return func(*args, **kwargs)

        if not is_logged_in():
            # Redirect to signup page.
            return redirect(create_login_url(request.url))

        # Nope, user isn't an admin.
        raise Forbidden()

    return decorated
