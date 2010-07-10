# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth.oauth
    ~~~~~~~~~~~~~~~~~~~~

    Implementation of OAuth authentication scheme.

    Ported from `tornado.auth <http://github.com/facebook/tornado/blob/master/tornado/auth.py>`_.

    :copyright: 2009 Facebook.
    :copyright: 2010 tipfy.org.
    :license: Apache License Version 2.0, see LICENSE.txt for more details.
"""
from __future__ import absolute_import
import binascii
import cgi
import functools
import hashlib
import hmac
import logging
import time
import urllib
import urlparse
import uuid

from google.appengine.api import urlfetch

from tipfy import abort, redirect


class OAuthMixin(object):
    """A :class:`tipfy.RequestHandler` mixin that implements OAuth
    authentication."""

    _OAUTH_AUTHORIZE_URL = None
    _OAUTH_NO_CALLBACKS = False

    def authorize_redirect(self, callback_uri=None, oauth_authorize_url=None):
        """Redirects the user to obtain OAuth authorization for this service.

        Twitter and FriendFeed both require that you register a Callback
        URL with your application. You should call this method to log the
        user in, and then call get_authenticated_user() in the handler
        you registered as your Callback URL to complete the authorization
        process.

        This method sets a cookie called _oauth_request_token which is
        subsequently used (and cleared) in get_authenticated_user for
        security purposes.

        :param callback_uri:
        :param oauth_authorize_url:
            OAuth authorization URL. If not set, uses the value set in
            :attr:`_OAUTH_AUTHORIZE_URL`.
        :return:
        """
        if callback_uri and getattr(self, '_OAUTH_NO_CALLBACKS', False):
            raise Exception('This service does not support oauth_callback')

        oauth_authorize_url = oauth_authorize_url or self._OAUTH_AUTHORIZE_URL

        url = self._oauth_request_token_url()
        try:
            response = urlfetch.fetch(url, deadline=10)
        except urlfetch.DownloadError, e:
            logging.exception(e)
            response = None

        return self._on_request_token(oauth_authorize_url, callback_uri,
            response)

    def get_authenticated_user(self, callback):
        """Gets the OAuth authorized user and access token on callback.

        This method should be called from the handler for your registered
        OAuth Callback URL to complete the registration process. We call
        callback with the authenticated user, which in addition to standard
        attributes like 'name' includes the 'access_key' attribute, which
        contains the OAuth access you can use to make authorized requests
        to this service on behalf of the user.

        :param callback:
        :return:
        """
        request_key = self.request.args.get('oauth_token')
        request_cookie = self.request.cookies.get('_oauth_request_token')
        if not request_cookie:
            logging.warning('Missing OAuth request token cookie')
            return callback(None)

        cookie_key, cookie_secret = request_cookie.split('|')
        if cookie_key != request_key:
            logging.warning('Request token does not match cookie')
            return callback(None)

        token = dict(key=cookie_key, secret=cookie_secret)
        url = self._oauth_access_token_url(token)

        try:
            response = urlfetch.fetch(url, deadline=10)
            if response.status_code < 200 or response.status_code >= 300:
                logging.warning('Invalid OAuth response: %s',
                    response.content)
                response = None
        except urlfetch.DownloadError, e:
            logging.exception(e)
            response = None

        return self._on_access_token(callback, response)

    def _oauth_request_token_url(self):
        """

        :return:
        """
        consumer_token = self._oauth_consumer_token()
        url = self._OAUTH_REQUEST_TOKEN_URL
        args = dict(
            oauth_consumer_key=consumer_token['key'],
            oauth_signature_method='HMAC-SHA1',
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=binascii.b2a_hex(uuid.uuid4().bytes),
            oauth_version='1.0',
        )
        signature = _oauth_signature(consumer_token, 'GET', url, args)
        args['oauth_signature'] = signature
        return url + '?' + urllib.urlencode(args)

    def _on_request_token(self, authorize_url, callback_uri, response):
        """
        :param authorize_url:
        :param callback_uri:
        :param response:
        :return:
        """
        if not response:
            logging.warning('Could not get OAuth request token.')
            abort(500)
        elif response.status_code < 200 or response.status_code >= 300:
            logging.warning('Invalid OAuth response (%d): %s',
                response.status_code, response.content)
            abort(500)

        request_token = _oauth_parse_response(response.content)
        data = '|'.join([request_token['key'], request_token['secret']])
        self.set_cookie('_oauth_request_token', data)
        args = dict(oauth_token=request_token['key'])
        if callback_uri:
            args['oauth_callback'] = urlparse.urljoin(
                self.request.url, callback_uri)

        return redirect(authorize_url + '?' + urllib.urlencode(args))

    def _oauth_access_token_url(self, request_token):
        """
        :param request_token:
        :return:
        """
        consumer_token = self._oauth_consumer_token()
        url = self._OAUTH_ACCESS_TOKEN_URL
        args = dict(
            oauth_consumer_key=consumer_token['key'],
            oauth_token=request_token['key'],
            oauth_signature_method='HMAC-SHA1',
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=binascii.b2a_hex(uuid.uuid4().bytes),
            oauth_version='1.0',
        )
        signature = _oauth_signature(consumer_token, 'GET', url, args,
                                     request_token)
        args['oauth_signature'] = signature
        return url + '?' + urllib.urlencode(args)

    def _on_access_token(self, callback, response):
        """
        :param callback:
        :param response:
        :return:
        """
        if not response:
            logging.warning('Missing OAuth access token response.')
            return callback(None)
        elif response.status_code < 200 or response.status_code >= 300:
            logging.warning('Invalid OAuth access token response (%d): %s',
                response.status_code, response.content)
            return callback(None)

        access_token = _oauth_parse_response(response.content)
        return self._oauth_get_user(access_token, functools.partial(
             self._on_oauth_get_user, access_token, callback))

    def _oauth_get_user(self, access_token, callback):
        """
        :param access_token:
        :param callback:
        :return:
        """
        raise NotImplementedError()

    def _on_oauth_get_user(self, access_token, callback, user):
        """
        :param access_token:
        :param callback:
        :param user:
        :return:
        """
        if not user:
            callback(None)
            return

        user['access_token'] = access_token
        return callback(user)

    def _oauth_request_parameters(self, url, access_token, parameters={},
                                  method='GET'):
        """Returns the OAuth parameters as a dict for the given request.

        parameters should include all POST arguments and query string arguments
        that will be sent with the request.

        :param url:
        :param access_token:
        :param parameters:
        :param method:
        :return:
        """
        consumer_token = self._oauth_consumer_token()
        base_args = dict(
            oauth_consumer_key=consumer_token['key'],
            oauth_token=access_token['key'],
            oauth_signature_method='HMAC-SHA1',
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=binascii.b2a_hex(uuid.uuid4().bytes),
            oauth_version='1.0',
        )
        args = {}
        args.update(base_args)
        args.update(parameters)
        signature = _oauth_signature(consumer_token, method, url, args,
                                     access_token)
        base_args['oauth_signature'] = signature
        return base_args


def _oauth_signature(consumer_token, method, url, parameters={}, token=None):
    """Calculates the HMAC-SHA1 OAuth signature for the given request.

    See http://oauth.net/core/1.0/#signing_process

    :param consumer_token:
    :param method:
    :param url:
    :param parameters:
    :param token:
    :return:
    """
    parts = urlparse.urlparse(url)
    scheme, netloc, path = parts[:3]
    normalized_url = scheme.lower() + '://' + netloc.lower() + path

    base_elems = []
    base_elems.append(method.upper())
    base_elems.append(normalized_url)
    base_elems.append('&'.join('%s=%s' % (k, _oauth_escape(str(v)))
                               for k, v in sorted(parameters.items())))
    base_string =  '&'.join(_oauth_escape(e) for e in base_elems)

    key_elems = [consumer_token['secret']]
    key_elems.append(token['secret'] if token else '')
    key = '&'.join(key_elems)

    hash = hmac.new(key, base_string, hashlib.sha1)
    return binascii.b2a_base64(hash.digest())[:-1]


def _oauth_escape(val):
    """
    :param val:
    :return:
    """
    if isinstance(val, unicode):
        val = val.encode('utf-8')

    return urllib.quote(val, safe='~')


def _oauth_parse_response(body):
    """
    :param body:
    :return:
    """
    p = cgi.parse_qs(body, keep_blank_values=False)
    token = dict(key=p['oauth_token'][0], secret=p['oauth_token_secret'][0])

    # Add the extra parameters the Provider included to the token
    special = ('oauth_token', 'oauth_token_secret')
    token.update((k, p[k][0]) for k in p if k not in special)
    return token
