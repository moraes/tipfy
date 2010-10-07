# -*- coding: utf-8 -*-
"""
    tipfy.appengine.auth
    ~~~~~~~~~~~~~~~~~~~~

    App Engine authentication backends.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from google.appengine.api import users

from werkzeug import cached_property

from tipfy.auth import BaseAuthStore, SessionAuthStore


class AuthStore(BaseAuthStore):
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


class MixedAuthStore(SessionAuthStore):
    """This stores uses App Engine auth mixed with own session, allowing
    cross-subdomain auth.
    """
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
        session_token = session.get('token')
        if user is None or session_token is None:
            if gae_user:
                if user:
                    return self._set_session(auth_id, user, user.auth_remember)
                else:
                    return self._set_session(auth_id)

            # Bad auth id or token, no fallback: must log in again.
            return self.logout()

        current_token = user.session_id
        if not user.check_session(session_token):
            # Token didn't match.
            return self.logout()

        # Successful login. Check if session id needs renewal.
        user.renew_session(max_age=self.config['session_max_age'])

        if (current_token != user.session_id) or user.auth_remember:
            # Token was updated or we need to renew session per request.
            self._set_session(auth_id, user, user.auth_remember)

        self._user = user


def gae_user_to_dict(user):
    return {
        'nickname':           user.nickname(),
        'email':              user.email(),
        'user_id':            user.user_id(),
        'federated_identity': user.federated_identity(),
        'federated_provider': user.federated_provider(),
    }
