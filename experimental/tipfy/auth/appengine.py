# -*- coding: utf-8 -*-
"""
    tipfy.auth.appengine
    ~~~~~~~~~~~~~~~~~~~~

    App Engine authentication backends.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import absolute_import

from google.appengine.api import users

from werkzeug import cached_property

from tipfy.auth import BaseAuthStore


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

    def create_user(self, username, **kwargs):
        auth_id = self._session_base.get('_auth', {}).get('id')
        if not auth_id:
            return

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

    def _set_session(self, auth_id, user=None):
        kwargs = self.app.get_config('tipfy.sessions', 'cookie_args').copy()
        kwargs['max_age'] = None

        session = {'id': auth_id}
        if user:
            session['token'] = user.session_id
            if user.auth_remember:
                kwargs['max_age'] = self.config.get('session_max_age')

        self._session_base['_auth'] = self._session = session
        self.request.session_store.set_session(self.config.get('cookie_name'),
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
