# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth.facebook
    ~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of Facebook authentication scheme.

    Ported from `tornado.auth <http://github.com/facebook/tornado/blob/master/tornado/auth.py>`_.

    :copyright: 2009 Facebook.
    :copyright: 2010 tipfy.org.
    :license: Apache License Version 2.0, see LICENSE.txt for more details.
"""
import urlparse
import urllib

from tipfy import redirect, REQUIRED_VALUE

#: Default configuration values for this module. Keys are:
#:
#: - ``facebook_api_key``:
#: - ``facebook_secret``:
default_config = {
    'facebook_api_key': REQUIRED_VALUE,
    'facebook_secret':  REQUIRED_VALUE,
}


class FacebookMixin(object):
    """A :class:`tipfy.RequestHandler` mixin that implements Facebook Connect
    authentication.

    To authenticate with Facebook, register your application with
    Facebook at http://www.facebook.com/developers/apps.php. Then
    copy your API Key and Application Secret to the application settings
    'facebook_api_key' and 'facebook_secret'.

    When your application is set up, you can use this Mixin like this
    to authenticate the user with Facebook:

    class FacebookHandler(tipfy.RequestHandler,
                          tipfy.ext.auth.FacebookMixin):
        def get(self):
            if self.get_argument('session', None):
                self.get_authenticated_user(self._on_auth)
                return

            self.authenticate_redirect()

        def _on_auth(self, user):
            if not user:
                raise tornado.web.HTTPError(500, 'Facebook auth failed')
            # Save the user using, e.g., set_secure_cookie()

    The user object returned by get_authenticated_user() includes the
    attributes 'facebook_uid' and 'name' in addition to session attributes
    like 'session_key'. You should save the session key with the user; it is
    required to make requests on behalf of the user later with
    facebook_request().
    """
    @property
    def _facebook_api_key(self):
        self.app.get_config(__name__, 'facebook_api_key')

    @property
    def _facebook_secret(self):
        self.app.get_config(__name__, 'facebook_secret')

    def authenticate_redirect(self, callback_uri=None, cancel_uri=None,
                              extended_permissions=None):
        """Authenticates/installs this app for the current user."""
        callback_uri = callback_uri or self.request.path
        args = {
            'api_key':        self._facebook_api_key,
            'v':              '1.0',
            'fbconnect':      'true',
            'display':        'page',
            'next':           urlparse.urljoin(self.request.url, callback_uri),
            'return_session': 'true',
        }
        if cancel_uri:
            args['cancel_url'] = urlparse.urljoin(self.request.url, cancel_uri)

        if extended_permissions:
            if isinstance(extended_permissions, basestring):
                extended_permissions = [extended_permissions]

            args['req_perms'] = ','.join(extended_permissions)

        return redirect('http://www.facebook.com/login.php?' +
                        urllib.urlencode(args))

    def authorize_redirect(self, extended_permissions, callback_uri=None,
                           cancel_uri=None):
        """Redirects to an authorization request for the given FB resource.

        The available resource names are listed at
        http://wiki.developers.facebook.com/index.php/Extended_permission.
        The most common resource types include:

            publish_stream
            read_stream
            email
            sms

        extended_permissions can be a single permission name or a list of
        names. To get the session secret and session key, call
        get_authenticated_user() just as you would with
        authenticate_redirect().
        """
        return self.authenticate_redirect(callback_uri, cancel_uri,
                                          extended_permissions)

    def get_authenticated_user(self, callback):
        """Fetches the authenticated Facebook user.

        The authenticated user includes the special Facebook attributes
        'session_key' and 'facebook_uid' in addition to the standard
        user attributes like 'name'.
        """
        session = escape.json_decode(self.get_argument('session'))
        self.facebook_request(
            method='facebook.users.getInfo',
            callback=functools.partial(
                self._on_get_user_info, callback, session),
            session_key=session['session_key'],
            uids=session['uid'],
            fields='uid,first_name,last_name,name,locale,pic_square,' \
                   'profile_url,username')

    def facebook_request(self, method, callback, **args):
        """Makes a Facebook API REST request.

        We automatically include the Facebook API key and signature, but
        it is the callers responsibility to include 'session_key' and any
        other required arguments to the method.

        The available Facebook methods are documented here:
        http://wiki.developers.facebook.com/index.php/API

        Here is an example for the stream.get() method:

        class MainHandler(tipfy.RequestHandler,
                          tipfy.ext.auth.FacebookMixin):
            def get(self):
                self.facebook_request(
                    method='stream.get',
                    callback=self._on_stream,
                    session_key=self.current_user['session_key'])

            def _on_stream(self, stream):
                if stream is None:
                   # Not authorized to read the stream yet?
                   self.redirect(self.authorize_redirect('read_stream'))
                   return
                self.render('stream.html', stream=stream)

        """
        if not method.startswith('facebook.'):
            method = 'facebook.' + method
        args['api_key'] = self._facebook_api_key
        args['v'] = '1.0'
        args['method'] = method
        args['call_id'] = str(long(time.time() * 1e6))
        args['format'] = 'json'
        args['sig'] = self._signature(args)
        url = 'http://api.facebook.com/restserver.php?' + \
            urllib.urlencode(args)
        http = httpclient.AsyncHTTPClient()
        http.fetch(url, callback=functools.partial(
            self._parse_response, callback))

    def _on_get_user_info(self, callback, session, users):
        if users is None:
            callback(None)
            return

        user = users[0]
        callback({
            'name':            user['name'],
            'first_name':      user['first_name'],
            'last_name':       user['last_name'],
            'uid':             user['uid'],
            'locale':          user['locale'],
            'pic_square':      user['pic_square'],
            'profile_url':     user['profile_url'],
            'username':        user.get('username'),
            'session_key':     session['session_key'],
            'session_expires': session.get('expires'),
        })

    def _parse_response(self, callback, response):
        if response.error:
            logging.warning('HTTP error from Facebook: %s', response.error)
            callback(None)
            return
        try:
            json = escape.json_decode(response.content)
        except:
            logging.warning('Invalid JSON from Facebook: %r', response.content)
            callback(None)
            return
        if isinstance(json, dict) and json.get('error_code'):
            logging.warning('Facebook error: %d: %r', json['error_code'],
                            json.get('error_msg'))
            callback(None)
            return
        callback(json)

    def _signature(self, args):
        parts = ['%s=%s' % (n, args[n]) for n in sorted(args.keys())]
        body = ''.join(parts) + self._facebook_secret
        if isinstance(body, unicode): body = body.encode('utf-8')
        return hashlib.md5(body).hexdigest()
