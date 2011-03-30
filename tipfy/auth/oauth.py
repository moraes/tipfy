# -*- coding: utf-8 -*-
"""
    tipfy.auth.oauth
    ~~~~~~~~~~~~~~~~

    Implementation of OAuth authentication scheme.

    Ported from `tornado.auth`_ and python-oauth2.

    :copyright: 2007 Leah Culver.
    :copyright: 2009 Facebook.
    :copyright: 2011 tipfy.org.
    :license: MIT License / Apache License Version 2.0, see LICENSE.txt for
        more details.
"""
from __future__ import absolute_import

import base64
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


class OAuthMixin(object):
    """A :class:`tipfy.RequestHandler` mixin that implements OAuth
    authentication.
    """
    _OAUTH_VERSION = '1.0a'
    _OAUTH_NO_CALLBACKS = False

    def authorize_redirect(self, callback_uri=None, extra_params=None):
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
        :returns:
        """
        if callback_uri and self._OAUTH_NO_CALLBACKS:
            raise Exception('This service does not support oauth_callback.')

        if self._OAUTH_VERSION == '1.0a':
            url = self._oauth_request_token_url(callback_uri=callback_uri,
                extra_params=extra_params)
        else:
            url = self._oauth_request_token_url()

        try:
            response = urlfetch.fetch(url, deadline=10)
        except urlfetch.DownloadError, e:
            logging.exception(e)
            response = None

        return self._on_request_token(self._OAUTH_AUTHORIZE_URL, callback_uri,
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
        :returns:
        """
        request_key = self.request.args.get('oauth_token')
        oauth_verifier = self.request.args.get('oauth_verifier', None)
        request_cookie = self.request.cookies.get('_oauth_request_token')

        if request_cookie:
            parts = request_cookie.split('|')
            if len(parts) == 2:
                try:
                    cookie_key = base64.b64decode(parts[0])
                    cookie_secret = base64.b64decode(parts[1])
                except TypeError, e:
                    # TypeError: Incorrect padding
                    logging.exception(e)
                    request_cookie = None
            else:
                request_cookie = None

        if not request_cookie:
            return callback(None)

        self.session_store.delete_cookie('_oauth_request_token')

        if cookie_key != request_key:
            return callback(None)

        token = dict(key=cookie_key, secret=cookie_secret)
        if oauth_verifier:
            token['verifier'] = oauth_verifier

        try:
            url = self._oauth_access_token_url(token)
            response = urlfetch.fetch(url, deadline=10)
        except urlfetch.DownloadError, e:
            logging.exception(e)
            response = None

        return self._on_access_token(callback, response)

    def _oauth_request_token_url(self, callback_uri=None, extra_params=None):
        """

        :returns:
        """
        consumer_token = self._oauth_consumer_token()
        url = self._OAUTH_REQUEST_TOKEN_URL
        args = dict(
            oauth_consumer_key=consumer_token['key'],
            oauth_signature_method='HMAC-SHA1',
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=binascii.b2a_hex(uuid.uuid4().bytes),
            oauth_version=self._OAUTH_VERSION
        )

        if self._OAUTH_VERSION == '1.0a':
            if callback_uri:
                args['oauth_callback'] = urlparse.urljoin(self.request.url,
                    callback_uri)

            if extra_params:
                args.update(extra_params)

        signature = _oauth_signature(consumer_token, 'GET', url, args)
        args['oauth_signature'] = signature
        return url + '?' + urllib.urlencode(args)

    def _on_request_token(self, authorize_url, callback_uri, response):
        """
        :param authorize_url:
        :param callback_uri:
        :param response:
        :returns:
        """
        if not response:
            logging.warning('Could not get OAuth request token.')
            self.abort(500)
        elif response.status_code < 200 or response.status_code >= 300:
            logging.warning('Bad OAuth response when requesting a token '
                '(%d): %s', response.status_code, response.content)
            self.abort(500)

        request_token = _oauth_parse_response(response.content)
        data = '|'.join([base64.b64encode(request_token['key']),
            base64.b64encode(request_token['secret'])])
        self.session_store.set_cookie('_oauth_request_token', data)
        args = dict(oauth_token=request_token['key'])

        if callback_uri:
            args['oauth_callback'] = urlparse.urljoin(
                self.request.url, callback_uri)

        return self.redirect(authorize_url + '?' + urllib.urlencode(args))

    def _oauth_access_token_url(self, request_token):
        """
        :param request_token:
        :returns:
        """
        consumer_token = self._oauth_consumer_token()
        url = self._OAUTH_ACCESS_TOKEN_URL
        args = dict(
            oauth_consumer_key=consumer_token['key'],
            oauth_token=request_token['key'],
            oauth_signature_method='HMAC-SHA1',
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=binascii.b2a_hex(uuid.uuid4().bytes),
            oauth_version=self._OAUTH_VERSION,
        )
        if 'verifier' in request_token:
            args['oauth_verifier']=request_token['verifier']

        signature = _oauth_signature(consumer_token, 'GET', url, args,
            request_token)
        args['oauth_signature'] = signature
        return url + '?' + urllib.urlencode(args)

    def _on_access_token(self, callback, response):
        """
        :param callback:
        :param response:
        :returns:
        """
        if not response:
            logging.warning('Could not get OAuth access token.')
            self.abort(500)
        elif response.status_code < 200 or response.status_code >= 300:
            logging.warning('Bad OAuth response trying to get access token '
                '(%d): %s', response.status_code, response.content)
            self.abort(500)

        access_token = _oauth_parse_response(response.content)
        return self._oauth_get_user(access_token, functools.partial(
             self._on_oauth_get_user, access_token, callback))

    def _oauth_get_user(self, access_token, callback):
        """
        :param access_token:
        :param callback:
        :returns:
        """
        raise NotImplementedError()

    def _on_oauth_get_user(self, access_token, callback, user):
        """
        :param access_token:
        :param callback:
        :param user:
        :returns:
        """
        if not user:
            return callback(None)

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
        :returns:
        """
        consumer_token = self._oauth_consumer_token()
        base_args = dict(
            oauth_consumer_key=consumer_token['key'],
            oauth_token=access_token['key'],
            oauth_signature_method='HMAC-SHA1',
            oauth_timestamp=str(int(time.time())),
            oauth_nonce=binascii.b2a_hex(uuid.uuid4().bytes),
            oauth_version=self._OAUTH_VERSION,
        )
        args = {}
        args.update(base_args)
        args.update(parameters)
        signature = _oauth_signature(consumer_token, method, url, args,
            access_token)
        base_args['oauth_signature'] = signature
        return base_args


class OAuth2Mixin(object):
    """Abstract implementation of OAuth v 2."""

    def authorize_redirect(self, redirect_uri=None, client_id=None,
        client_secret=None, extra_params=None):
        """Redirects the user to obtain OAuth authorization for this service.

        Some providers require that you register a Callback
        URL with your application. You should call this method to log the
        user in, and then call get_authenticated_user() in the handler
        you registered as your Callback URL to complete the authorization
        process.
        """
        args = {
            'redirect_uri': redirect_uri,
            'client_id': client_id
        }
        if extra_params:
            args.update(extra_params)

        return self.redirect(self._OAUTH_AUTHORIZE_URL +
            urllib.urlencode(args))

    def _oauth_request_token_url(self, redirect_uri= None, client_id = None,
        client_secret=None, code=None, extra_params=None):
        url = self._OAUTH_ACCESS_TOKEN_URL
        args = dict(
            redirect_uri=redirect_uri,
            code=code,
            client_id=client_id,
            client_secret=client_secret,
        )
        if extra_params:
            args.update(extra_params)

        return url + urllib.urlencode(args)


def _to_utf8(s):
    if isinstance(s, unicode):
        return s.encode('utf-8')

    return s


def _split_url_string(param_str):
    """Turn URL string into parameters."""
    parameters = cgi.parse_qs(param_str.encode('utf-8'), keep_blank_values=True)
    res = {}
    for k, v in parameters.iteritems():
        res[k] = urllib.unquote(v[0])

    return res


def _get_normalized_parameters(parameters, query):
    """Return a string that contains the parameters that must be signed."""
    items = []
    for key, value in parameters.iteritems():
        if key == 'oauth_signature':
            continue
        # 1.0a/9.1.1 states that kvp must be sorted by key, then by value,
        # so we unpack sequence values into multiple items for sorting.
        if isinstance(value, basestring):
            items.append((_to_utf8(key), _to_utf8(value)))
        else:
            try:
                value = list(value)
            except TypeError, e:
                assert 'is not iterable' in str(e)
                items.append((_to_utf8(key), _to_utf8(value)))
            else:
                items.extend((_to_utf8(key), _to_utf8(item)) for item in value)

    url_items = _split_url_string(query).items()
    url_items = [(_to_utf8(k), _to_utf8(v))
        for k, v in url_items if k != 'oauth_signature']
    items.extend(url_items)
    items.sort()
    encoded_str = urllib.urlencode(items)
    # Encode signature parameters per Oauth Core 1.0 protocol
    # spec draft 7, section 3.6
    # (http://tools.ietf.org/html/draft-hammer-oauth-07#section-3.6)
    # Spaces must be encoded with "%20" instead of "+"
    return encoded_str.replace('+', '%20').replace('%7E', '~')


def _oauth_signature(consumer_token, method, url, parameters={}, token=None):
    """Calculates the HMAC-SHA1 OAuth signature for the given request.

    See http://oauth.net/core/1.0/#signing_process

    :param consumer_token:
    :param method:
    :param url:
    :param parameters:
    :param token:
    :returns:
    """
    parts = urlparse.urlparse(url)
    scheme, netloc, path = parts[:3]
    query = parts[4]
    normalized_url = scheme.lower() + '://' + netloc.lower() + path

    sig = (
        _oauth_escape(method),
        _oauth_escape(normalized_url),
        _oauth_escape(_get_normalized_parameters(parameters, query)),
    )

    key = '%s&' % _oauth_escape(consumer_token['secret'])
    if token:
        key += _oauth_escape(token['secret'])

    base_string = '&'.join(sig)
    hashed = hmac.new(key, base_string, hashlib.sha1)
    return binascii.b2a_base64(hashed.digest())[:-1]


def _oauth_escape(val):
    """
    :param val:
    :returns:
    """
    if isinstance(val, unicode):
        val = val.encode('utf-8')

    return urllib.quote(val, safe='~')


def _oauth_parse_response(body):
    """
    :param body:
    :returns:
    """
    p = cgi.parse_qs(body, keep_blank_values=False)
    token = dict(key=p['oauth_token'][0], secret=p['oauth_token_secret'][0])

    # Add the extra parameters the Provider included to the token
    special = ('oauth_token', 'oauth_token_secret')
    token.update((k, p[k][0]) for k in p if k not in special)
    return token
