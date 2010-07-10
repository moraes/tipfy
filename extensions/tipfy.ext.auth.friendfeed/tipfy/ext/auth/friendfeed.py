# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth.friendfeed
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of FriendFeed authentication scheme.

    Ported from `tornado.auth <http://github.com/facebook/tornado/blob/master/tornado/auth.py>`_.

    :copyright: 2009 Facebook.
    :copyright: 2010 tipfy.org.
    :license: Apache License Version 2.0, see LICENSE.txt for more details.
"""
from __future__ import absolute_import
import functools
import logging
import urllib

from google.appengine.api import urlfetch

from django.utils import simplejson

from tipfy import REQUIRED_VALUE
from tipfy.ext.auth.oauth import OAuthMixin

#: Default configuration values for this module. Keys are:
#:
#: - ``consumer_key``: Key provided when you register an application with
#:   FriendFeed.
#: - ``consumer_secret``: Secret provided when you register an application
#:   with FriendFeed.
default_config = {
    'consumer_key':    REQUIRED_VALUE,
    'consumer_secret': REQUIRED_VALUE,
}


class FriendFeedMixin(OAuthMixin):
    """A :class:`tipfy.RequestHandler` mixin that implements FriendFeed OAuth
    authentication.

    To authenticate with FriendFeed, register your application with
    FriendFeed at http://friendfeed.com/api/applications. Then
    copy your Consumer Key and Consumer Secret to config.py:

    <<code python>>
    config['tipfy.ext.auth.friendfeed'] = {
        'consumer_key':    'XXXXXXXXXXXXXXX',
        'consumer_secret': 'XXXXXXXXXXXXXXX',
    }
    <</code>>

    When your application is set up, you can use the FriendFeedMixin to
    authenticate the user with FriendFeed and get access to their stream.
    You must use the mixin on the handler for the URL you registered as your
    application's Callback URL. For example:

    <<code python>>
    from tipfy import RequestHandler, abort
    from tipfy.ext.auth.friendfeed import FriendFeedMixin

    class FriendFeedHandler(RequestHandler, FriendFeedMixin):
        def get(self):
            if self.request.args.get('oauth_token', None):
                return self.get_authenticated_user(self._on_auth)

            return self.authorize_redirect()

        def _on_auth(self, user):
            if not user:
                abort(403)

            # Set the user in the session.
            # ...
    <</code>>

    The user object returned by get_authenticated_user() includes the
    attributes 'username', 'name', and 'description' in addition to
    'access_token'. You should save the access token with the user;
    it is required to make requests on behalf of the user later with
    friendfeed_request().
    """
    _OAUTH_REQUEST_TOKEN_URL = 'https://friendfeed.com/account/oauth/request_token'
    _OAUTH_ACCESS_TOKEN_URL = 'https://friendfeed.com/account/oauth/access_token'
    _OAUTH_AUTHORIZE_URL = 'https://friendfeed.com/account/oauth/authorize'
    _OAUTH_NO_CALLBACKS = True

    @property
    def _friendfeed_consumer_key(self):
        return self.app.get_config(__name__, 'consumer_key')

    @property
    def _friendfeed_consumer_secret(self):
        return self.app.get_config(__name__, 'consumer_secret')

    def friendfeed_request(self, path, callback, access_token=None,
                           post_args=None, **args):
        """Fetches the given relative API path, e.g., '/bret/friends'

        If the request is a POST, post_args should be provided. Query
        string arguments should be given as keyword arguments.

        All the FriendFeed methods are documented at
        http://friendfeed.com/api/documentation.

        Many methods require an OAuth access token which you can obtain
        through authorize_redirect() and get_authenticated_user(). The
        user returned through that process includes an 'access_token'
        attribute that can be used to make authenticated requests via
        this method. Example usage:

        from tipfy import RequestHandler, Response
        from tipfy.ext.auth.friendfeed import FriendFeedMixin

        class MainHandler(RequestHandler, FriendFeedMixin):
            def get(self):
                return self.friendfeed_request('/entry',
                    post_args={'body': 'Testing Tornado Web Server'},
                    access_token=self.current_user['access_token'],
                    callback=self._on_post)

            def _on_post(self, new_entry):
                if not new_entry:
                    # Call failed; perhaps missing permission?
                    return self.authorize_redirect()

                return Response('Posted a message!')

        """
        # Add the OAuth resource request signature if we have credentials
        url = 'http://friendfeed-api.com/v2' + path
        if access_token:
            all_args = {}
            all_args.update(args)
            all_args.update(post_args or {})
            consumer_token = self._oauth_consumer_token()
            method = 'POST' if post_args is not None else 'GET'
            oauth = self._oauth_request_parameters(
                url, access_token, all_args, method=method)
            args.update(oauth)

        if args:
            url += '?' + urllib.urlencode(args)

        try:
            if post_args is not None:
                response = urlfetch.fetch(url, method='POST',
                    payload=urllib.urlencode(post_args), deadline=10)
            else:
                response = urlfetch.fetch(url, deadline=10)
        except urlfetch.DownloadError, e:
            logging.exception(e)
            response = None

        return self._on_friendfeed_request(callback, response)

    def _on_friendfeed_request(self, callback, response):
        if not response:
            logging.warning('Could not get a FriendFeed response.')
            return callback(None)
        elif response.status_code < 200 or response.status_code >= 300:
            logging.warning('Invalid FriendFeed response (%d): %s',
                response.status_code, response.content)
            return callback(None)

        return callback(simplejson.loads(response.content))

    def _oauth_consumer_token(self):
        return dict(
            key=self._friendfeed_consumer_key,
            secret=self._friendfeed_consumer_secret)

    def _oauth_get_user(self, access_token, callback):
        callback = functools.partial(self._parse_user_response, callback)
        return self.friendfeed_request(
            '/feedinfo/' + access_token['username'],
            include='id,name,description', access_token=access_token,
            callback=callback)

    def _parse_user_response(self, callback, user):
        if user:
            user['username'] = user['id']

        return callback(user)
