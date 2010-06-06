# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth.providers.oauth
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of OAuth authentication scheme.

    Ported from `tornado.auth <http://github.com/facebook/tornado/blob/master/tornado/auth.py>`_.

    :copyright: 2009 Facebook.
    :copyright: 2010 tipfy.org.
    :license: Apache License Version 2.0, see LICENSE.txt for more details.
"""
import functools
import urllib
import urlparse

from tipfy import RequestRedirect
from tipfy.ext.auth.providers import fetch_and_call


class OAuthMixin(object):
    """Abstract implementation of OAuth."""

    _OAUTH_AUTHORIZE_URL = None
    _OAUTH_NO_CALLBACKS = False

    def authorize_redirect(self, callback_uri=None):
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
        :return:
        """
        if callback_uri and getattr(self, '_OAUTH_NO_CALLBACKS', False):
            raise Exception('This service does not support oauth_callback')

        url = self._oauth_request_token_url()
        fetch_and_call(url, functools.partial(self._on_request_token,
            self._OAUTH_AUTHORIZE_URL, callback_uri))

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
        request_key = self.get_argument('oauth_token')
        request_cookie = self.get_cookie('_oauth_request_token')
        if not request_cookie:
            logging.warning('Missing OAuth request token cookie')
            callback(None)
            return

        cookie_key, cookie_secret = request_cookie.split('|')
        if cookie_key != request_key:
            logging.warning('Request token does not match cookie')
            callback(None)
            return

        token = dict(key=cookie_key, secret=cookie_secret)
        url = self._oauth_access_token_url(token)
        fetch_and_call(url, functools.partial(self._on_access_token, callback))

    def _oauth_request_token_url(self):
        """
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
        if response.error:
            raise Exception('Could not get request token')

        request_token = _oauth_parse_response(response.body)
        data = '|'.join([request_token['key'], request_token['secret']])
        self.set_cookie('_oauth_request_token', data)
        args = dict(oauth_token=request_token['key'])
        if callback_uri:
            args['oauth_callback'] = urlparse.urljoin(
                self.request.url, callback_uri)

        self.redirect(authorize_url + '?' + urllib.urlencode(args))

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
        if response.error:
            logging.warning('Could not fetch access token')
            callback(None)
            return

        access_token = _oauth_parse_response(response.body)
        user = self._oauth_get_user(access_token, self.async_callback(
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
        callback(user)

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
    p = urlparse.parse_qs(body, keep_blank_values=False)
    token = dict(key=p['oauth_token'][0], secret=p['oauth_token_secret'][0])

    # Add the extra parameters the Provider included to the token
    special = ('oauth_token', 'oauth_token_secret')
    token.update((k, p[k][0]) for k in p if k not in special)
    return token
