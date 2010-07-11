# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth.google
    ~~~~~~~~~~~~~~~~~~~~~

    Implementation of Google authentication scheme.

    Ported from `tornado.auth <http://github.com/facebook/tornado/blob/master/tornado/auth.py>`_.

    :copyright: 2009 Facebook.
    :copyright: 2010 tipfy.org.
    :license: Apache License Version 2.0, see LICENSE.txt for more details.
"""
from __future__ import absolute_import
import logging
import urllib

from google.appengine.api import urlfetch

from tipfy import redirect, REQUIRED_VALUE
from tipfy.ext.auth.oauth import OAuthMixin
from tipfy.ext.auth.openid import OpenIdMixin

#: Default configuration values for this module. Keys are:
#:
#: - ``google_consumer_key``:
#: - ``google_consumer_secret``:
default_config = {
    'google_consumer_key':    REQUIRED_VALUE,
    'google_consumer_secret': REQUIRED_VALUE,
}


class GoogleMixin(OpenIdMixin, OAuthMixin):
    """A :class:`tipfy.RequestHandler` mixin that implements Google OpenId /
    OAuth authentication.

    No application registration is necessary to use Google for authentication
    or to access Google resources on behalf of a user. To authenticate with
    Google, redirect with authenticate_redirect(). On return, parse the
    response with get_authenticated_user(). We send a dict containing the
    values for the user, including 'email', 'name', and 'locale'.
    Example usage:

    <<code python>>
    from tipfy import RequestHandler, abort
    from tipfy.ext.auth.google import GoogleMixin

    class GoogleHandler(RequestHandler, GoogleMixin):
        def get(self):
            if self.request.args.get('openid.mode', None):
                return self.get_authenticated_user(self._on_auth)

            return self.authenticate_redirect()

        def _on_auth(self, user):
            if not user:
                abort(403)

            # Set the user in the session.
    <</code>>
    """
    _OPENID_ENDPOINT = 'https://www.google.com/accounts/o8/ud'
    _OAUTH_ACCESS_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetAccessToken'

    @property
    def _google_consumer_key(self):
        return self.app.get_config(__name__, 'google_consumer_key')

    @property
    def _google_consumer_secret(self):
        return self.app.get_config(__name__, 'google_consumer_secret')

    def _oauth_consumer_token(self):
        return dict(
            key=self._google_consumer_key,
            secret=self._google_consumer_secret)

    def authorize_redirect(self, oauth_scope, callback_uri=None, ax_attrs=None):
        """Authenticates and authorizes for the given Google resource.

        Some of the available resources are:

           Gmail Contacts - http://www.google.com/m8/feeds/
           Calendar - http://www.google.com/calendar/feeds/
           Finance - http://finance.google.com/finance/feeds/

        You can authorize multiple resources by separating the resource
        URLs with a space.
        """
        callback_uri = callback_uri or self.request.path
        ax_attrs = ax_attrs or ['name','email','language','username']
        args = self._openid_args(callback_uri, ax_attrs=ax_attrs,
                                 oauth_scope=oauth_scope)
        return redirect(self._OPENID_ENDPOINT + '?' + urllib.urlencode(args))

    def get_authenticated_user(self, callback):
        """Fetches the authenticated user data upon redirect."""
        # Look to see if we are doing combined OpenID/OAuth
        oauth_ns = ''
        for name, values in self.request.args.iterlists():
            if name.startswith('openid.ns.') and \
                values[-1] == u'http://specs.openid.net/extensions/oauth/1.0':
                oauth_ns = name[10:]
                break

        token = self.request.args.get('openid.' + oauth_ns + '.request_token',
            '')
        if token:
            try:
                token = dict(key=token, secret='')
                url = self._oauth_access_token_url(token)
                response = urlfetch.fetch(url, deadline=10)
            except urlfetch.DownloadError, e:
                logging.exception(e)
                response = None

            return self._on_access_token(callback, response)
        else:
            return OpenIdMixin.get_authenticated_user(self, callback)

    def _oauth_get_user(self, access_token, callback):
        return OpenIdMixin.get_authenticated_user(self, callback)
