# -*- coding: utf-8 -*-
"""
    tipfy.ext.auth.providers.openid
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of OpenId authentication scheme.

    Ported from `tornado.auth <http://github.com/facebook/tornado/blob/master/tornado/auth.py>`_.

    :copyright: 2009 Facebook.
    :copyright: 2010 tipfy.org.
    :license: Apache License Version 2.0, see LICENSE.txt for more details.
"""
import functools
import logging
import urllib
import urlparse

from tipfy import RequestRedirect
from tipfy.ext.auth import urlfetch_and_call


class OpenIdMixin(object):
    """A :class:`tipfy.RequestHandler` mixin that implements OpenID
    authentication with Attribute Exchange.
    """

    #: OpenId provider endpoint. For example,
    #: 'https://www.google.com/accounts/o8/ud'
    _OPENID_ENDPOINT = None

    def authenticate_redirect(self, callback_uri=None, ax_attrs=None):
        """Returns the authentication URL for this service.

        After authentication, the service will redirect back to the given
        callback URI.

        We request the given attributes for the authenticated user by
        default (name, email, language, and username). If you don't need
        all those attributes for your app, you can request fewer with
        the ax_attrs keyword argument.

        :param callback_uri:
        :param ax_attrs:
        :return:
        """
        ax_attrs = ax_attrs or ['name', 'email', 'language', 'username']
        callback_uri = callback_uri or self.request.path
        args = self._openid_args(callback_uri, ax_attrs=ax_attrs)
        raise RequestRedirect(self._OPENID_ENDPOINT + '?' +
            urllib.urlencode(args))

    def get_authenticated_user(self, callback):
        """Fetches the authenticated user data upon redirect.

        This method should be called by the handler that receives the
        redirect from the authenticate_redirect() or authorize_redirect()
        methods.

        :param callback:
        :return:
        """
        # Verify the OpenID response via direct request to the OP
        args = dict((k, v[-1]) for k, v in self.request.args.lists())
        args['openid.mode'] = u'check_authentication'
        url = self._OPENID_ENDPOINT + '?' + urllib.urlencode(args)

        return urlfetch_and_call(url, functools.partial(
            self._on_authentication_verified, callback))

    def _openid_args(self, callback_uri, ax_attrs=None, oauth_scope=None):
        """

        :param callback_uri:
        :param ax_attrs:
        :param oauth_scope:
        :return:
        """
        url = urlparse.urljoin(self.request.url, callback_uri)
        args = {
            'openid.ns': 'http://specs.openid.net/auth/2.0',
            'openid.claimed_id':
                'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.identity':
                'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.return_to': url,
            'openid.realm': self.request.environ['wsgi.url_scheme'] + \
                '://' + self.request.host + '/',
            'openid.mode': 'checkid_setup',
        }
        if ax_attrs:
            args.update({
                'openid.ns.ax': 'http://openid.net/srv/ax/1.0',
                'openid.ax.mode': 'fetch_request',
            })
            ax_attrs = set(ax_attrs)
            required = []
            if 'name' in ax_attrs:
                ax_attrs -= set(['name', 'firstname', 'fullname', 'lastname'])
                required += ['firstname', 'fullname', 'lastname']
                args.update({
                    'openid.ax.type.firstname':
                        'http://axschema.org/namePerson/first',
                    'openid.ax.type.fullname':
                        'http://axschema.org/namePerson',
                    'openid.ax.type.lastname':
                        'http://axschema.org/namePerson/last',
                })

            known_attrs = {
                'email': 'http://axschema.org/contact/email',
                'language': 'http://axschema.org/pref/language',
                'username': 'http://axschema.org/namePerson/friendly',
            }

            for name in ax_attrs:
                args['openid.ax.type.' + name] = known_attrs[name]
                required.append(name)

            args['openid.ax.required'] = ','.join(required)

        if oauth_scope:
            args.update({
                'openid.ns.oauth':
                    'http://specs.openid.net/extensions/oauth/1.0',
                'openid.oauth.consumer': self.request.host.split(':')[0],
                'openid.oauth.scope': oauth_scope,
            })

        return args

    def _on_authentication_verified(self, callback, response):
        """

        :param callback:
        :param response:
        :return:
        """
        if response.error or u'is_valid:true' not in response.content:
            logging.warning('Invalid OpenID response: %s', response.error or
                            response.content)
            callback(None)
            return

        # Make sure we got back at least an email from attribute exchange
        ax_ns = None
        for name, values in self.request.args.iterlists():
            if name.startswith('openid.ns.') and \
               values[-1] == u'http://openid.net/srv/ax/1.0':
                ax_ns = name[10:]
                break

        _ax_args = {
            'email':      'http://axschema.org/contact/email',
            'name':       'http://axschema.org/namePerson',
            'first_name': 'http://axschema.org/namePerson/first',
            'last_name':  'http://axschema.org/namePerson/last',
            'username':   'http://axschema.org/namePerson/friendly',
            'locale':     'http://axschema.org/pref/language',
        }

        user = {}
        name_parts = []
        for name, uri in _ax_args.iteritems():
            value = self._get_ax_arg(uri, ax_ns)
            if value:
                user[name] = value
                if name in ('first_name', 'last_name'):
                    name_parts.append(value)

        if not user.get('name'):
            if name_parts:
                user['name'] = u' '.join(name_parts)
            elif user.get('email'):
                user['name'] = user.get('email').split('@', 1)[0]

        return callback(user)

    def _get_ax_arg(self, uri, ax_ns):
        """

        :param uri:
        :param ax_ns:
        :return:
        """
        if not ax_ns:
            return u''

        prefix = 'openid.' + ax_ns + '.type.'
        ax_name = None
        for name, values in self.request.args.iterlists():
            if values[-1] == uri and name.startswith(prefix):
                part = name[len(prefix):]
                ax_name = 'openid.' + ax_ns + '.value.' + part
                break

        if not ax_name:
            return u''

        return self.request.args.get(ax_name, u'')
