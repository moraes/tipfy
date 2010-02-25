# -*- coding: utf-8 -*-
"""
    tipfy.ext.user.auth.google_account
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Authentication using Google Account.

    This module derives from `Solace`_.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from google.appengine.api import users

from tipfy.ext.user.auth import BaseAuth


class GoogleAuth(BaseAuth):
    #: Used to identify the auth provider in user ids.
    auth_name = 'google'

    def authenticate_with_session(self, request):
        """Returns an authenticated user loaded from session or ``None``.

        :return:
            A tuple (user_id, nickname, email) if the user authenticated.
            Otherwise, `None`.
        """
        user = users.get_current_user()
        if user is None:
            return None

        return (user.user_id(), user.nickname(), user.email())

    def create_login_url(self, dest_url):
        """Returns the login URL for this request and specified destination URL.

        :param dest_url:
            String that is the desired final destination URL for the user once
            login is complete.
        :return:
            An URL to perform login.
        """
        return users.create_login_url(dest_url)

    def create_logout_url(self, dest_url):
        """Returns the logout URL for this request and specified destination
        URL.

        :param dest_url:
            String that is the desired final destination URL for the user once
            logout is complete.
        :return:
            An URL to perform logout.
        """
        return users.create_logout_url(dest_url)

    def is_logged_in(self):
        """Returns ``True`` if the current user is logged in.

        :return:
            ``True`` if the user for the current request is authenticated,
            ``False`` otherwise.
        """
        return (users.get_current_user() is not None)
