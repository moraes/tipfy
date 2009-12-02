# -*- coding: utf-8 -*-
"""
    tipfy.ext.user
    ~~~~~~~~~~~~~~

    User authentication and permissions extension.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import import_string, get_config

#: Default configuration values for this module. Keys are:
#:   - ``auth_system``: The default authentication class, as a string. Default
#:     is ``tipfy.ext.user.auth.google:GoogleAuth``.
#:   - ``user_model``: A subclass of ``db.Model`` used for authenticated users,.
#:     as a string. Default is ``tipfy.ext.user.models:User``.
default_config = {
    'auth_system': 'tipfy.ext.user.auth.google_account:GoogleAuth',
    'user_model':  'tipfy.ext.user.models:User',
}

#: Configured authentication system instance, cached in the module.
_auth_system = None


def set_auth(request, app):
    """Hook to initialize the authentication system. This will authenticate
    users and load the related :class:`tipfy.ext.user.models.User` entity from
    datastore.

    It is called on 'pre_dispatch_handler'.

    To enable it, add a hook to the list of hooks in ``config.py``:

    .. code-block:: python

       config = {
           'tipfy': {
               'hooks': {
                   'pre_dispatch_handler': ['tipfy.ext.user:set_auth'],
                   # ...
               },
           },
       }

    :param app:
        A :class:`tipfy.WSGIApplication` instance.
    :return:
        ``None``.
    """
    response = get_auth_system().load_user(request, app)
    if response is not None:
        return response


def get_auth_system():
    """Returns the configured authentication system.

    :return:
        An instance of :class:`tipfy.ext.user.auth.BaseAuth`.
    """
    global _auth_system
    if _auth_system is None:
        _auth_system = import_string(get_config(__name__, 'auth_system'))()

    return _auth_system


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
