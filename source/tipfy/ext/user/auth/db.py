# -*- coding: utf-8 -*-
"""
    tipfy.ext.user.auth.db
    ~~~~~~~~~~~~~~~~~~~~~~

    Authentication using datastore.

    This module derives from `Solace`_.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from datetime import datetime, timedelta

from werkzeug.contrib.securecookie import SecureCookie
from werkzeug import cookie_date

from tipfy import local, app, get_config
from tipfy.ext.user.auth import BaseAuth


class DbAuth(BaseAuth):
    """Datastore authentication adapter."""

    #: Used to identify the auth provider in user ids.
    auth_name = 'db'

    #: Set to True to indicate that this login system uses a password
    #: This will affect the account creation form.
    use_password = True

    def setup(self):
        """Sets up this adapter. This adds a hook to persist authentication
        sessions on each request.
        """
        app.hooks.add('pre_send_response', self.persist_authentication)

    def persist_authentication(self, response=None):
        """Sets the cookie that persists the authentication. This is used both
        for persistent ("remember me") and non-persistent (current session only)
        authentications.
        """
        if getattr(local, 'user_session', None) is not None:
            remember = local.user_session.get('remember', None)
            cookie_max_age = get_config('tipfy.ext.user', 'cookie_max_age')

            if remember == '1':
                # Persistent authentication.
                max_age = cookie_max_age
            else:
                # Non-persistent authentication (only lasts for this session).
                max_age = None

            # Set the cookie on each request, resetting the idle countdown.
            self.set_cookie(cookie_max_age, max_age)

    def authenticate_with_session(self):
        """Authenticates the current user using sessions."""
        # Check if session was set after form authentication.
        session = getattr(local, 'user_session', None)

        if session is None:
            # Load session from securecookie.
            session = SecureCookie.load_cookie(local.request,
                key=get_config('tipfy.ext.user', 'cookie_key'),
                secret_key=get_config('tipfy.ext.session', 'secret_key'))

        # Get the authentication id.
        auth_id = session.get('auth_id', None)
        if auth_id is None:
            return None

        # Store current secure cookie to persist later.
        local.user_session = session

        return (auth_id, None, None)

    def authenticate_with_form(self, username, password, remember=False):
        """Authenticates the current user using data from a form.

        :param username:
            Username.
        :param password:
            Password.
        :param remember:
            ``True`` if authentication should be persisted even if user leaves
            the current session (the "remember me" feature).
        :return:
            ``True`` if authentication was successful, ``False`` otherwise.
        """
        user = self.user_model.get_by_username(username)
        if user and user.check_password(password) is True:
            local.user_session = SecureCookie(data={
                'auth_id': user.auth_id,
                'remember': str(int(remember)),
            },
            secret_key=get_config('tipfy.ext.session', 'secret_key'))

            self.login()
            return True

        return False

    def is_logged_in(self):
        """Returns ``True`` if the current user is logged in.

        :return:
            ``True`` if the user for the current request is authenticated,
            ``False`` otherwise.
        """
        return (getattr(local, 'user_session', None) is not None)

    def logout(self):
        """Logs out the current user."""
        super(DbAuth, self).logout()

        if getattr(local, 'user_session', None) is not None:
            # Set cookie to the past.
            self.set_cookie(-86400, -86400)
            del local.user_session

    def set_cookie(self, session_expires, max_age):
        """Saves the authentication cookie."""
        session_expires = datetime.now() + timedelta(seconds=session_expires)

        local.user_session.save_cookie(local.response,
            session_expires=session_expires,
            max_age=max_age,
            key=get_config('tipfy.ext.user', 'cookie_key'),
            domain=get_config('tipfy.ext.user', 'cookie_domain'),
            path=get_config('tipfy.ext.user', 'cookie_path'),
            secure=get_config('tipfy.ext.user', 'cookie_secure'),
            httponly=get_config('tipfy.ext.user', 'cookie_httponly'),
            force=True
        )
