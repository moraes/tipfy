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
class OpenIdMixin(object):
    """Abstract implementation of OpenID and Attribute Exchange.

    See GoogleMixin below for example implementations.
    """
    def authenticate_redirect(self, callback_uri=None,
                              ax_attrs=["name","email","language","username"]):
        """Returns the authentication URL for this service.

        After authentication, the service will redirect back to the given
        callback URI.

        We request the given attributes for the authenticated user by
        default (name, email, language, and username). If you don't need
        all those attributes for your app, you can request fewer with
        the ax_attrs keyword argument.
        """
        callback_uri = callback_uri or self.request.path
        args = self._openid_args(callback_uri, ax_attrs=ax_attrs)
        self.redirect(self._OPENID_ENDPOINT + "?" + urllib.urlencode(args))

    def get_authenticated_user(self, callback):
        """Fetches the authenticated user data upon redirect.

        This method should be called by the handler that receives the
        redirect from the authenticate_redirect() or authorize_redirect()
        methods.
        """
        # Verify the OpenID response via direct request to the OP
        args = dict((k, v[-1]) for k, v in self.request.arguments.iteritems())
        args["openid.mode"] = u"check_authentication"
        url = self._OPENID_ENDPOINT + "?" + urllib.urlencode(args)
        http = httpclient.AsyncHTTPClient()
        http.fetch(url, self.async_callback(
            self._on_authentication_verified, callback))

    def _openid_args(self, callback_uri, ax_attrs=[], oauth_scope=None):
        url = urlparse.urljoin(self.request.full_url(), callback_uri)
        args = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.claimed_id":
                "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.identity":
                "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.return_to": url,
            "openid.realm": self.request.protocol + "://" + self.request.host + "/",
            "openid.mode": "checkid_setup",
        }
        if ax_attrs:
            args.update({
                "openid.ns.ax": "http://openid.net/srv/ax/1.0",
                "openid.ax.mode": "fetch_request",
            })
            ax_attrs = set(ax_attrs)
            required = []
            if "name" in ax_attrs:
                ax_attrs -= set(["name", "firstname", "fullname", "lastname"])
                required += ["firstname", "fullname", "lastname"]
                args.update({
                    "openid.ax.type.firstname":
                        "http://axschema.org/namePerson/first",
                    "openid.ax.type.fullname":
                        "http://axschema.org/namePerson",
                    "openid.ax.type.lastname":
                        "http://axschema.org/namePerson/last",
                })
            known_attrs = {
                "email": "http://axschema.org/contact/email",
                "language": "http://axschema.org/pref/language",
                "username": "http://axschema.org/namePerson/friendly",
            }
            for name in ax_attrs:
                args["openid.ax.type." + name] = known_attrs[name]
                required.append(name)
            args["openid.ax.required"] = ",".join(required)
        if oauth_scope:
            args.update({
                "openid.ns.oauth":
                    "http://specs.openid.net/extensions/oauth/1.0",
                "openid.oauth.consumer": self.request.host.split(":")[0],
                "openid.oauth.scope": oauth_scope,
            })
        return args

    def _on_authentication_verified(self, callback, response):
        if response.error or u"is_valid:true" not in response.body:
            logging.warning("Invalid OpenID response: %s", response.error or
                            response.body)
            callback(None)
            return

        # Make sure we got back at least an email from attribute exchange
        ax_ns = None
        for name, values in self.request.arguments.iteritems():
            if name.startswith("openid.ns.") and \
               values[-1] == u"http://openid.net/srv/ax/1.0":
                ax_ns = name[10:]
                break
        def get_ax_arg(uri):
            if not ax_ns: return u""
            prefix = "openid." + ax_ns + ".type."
            ax_name = None
            for name, values in self.request.arguments.iteritems():
                if values[-1] == uri and name.startswith(prefix):
                    part = name[len(prefix):]
                    ax_name = "openid." + ax_ns + ".value." + part
                    break
            if not ax_name: return u""
            return self.get_argument(ax_name, u"")

        email = get_ax_arg("http://axschema.org/contact/email")
        name = get_ax_arg("http://axschema.org/namePerson")
        first_name = get_ax_arg("http://axschema.org/namePerson/first")
        last_name = get_ax_arg("http://axschema.org/namePerson/last")
        username = get_ax_arg("http://axschema.org/namePerson/friendly")
        locale = get_ax_arg("http://axschema.org/pref/language").lower()
        user = dict()
        name_parts = []
        if first_name:
            user["first_name"] = first_name
            name_parts.append(first_name)
        if last_name:
            user["last_name"] = last_name
            name_parts.append(last_name)
        if name:
            user["name"] = name
        elif name_parts:
            user["name"] = u" ".join(name_parts)
        elif email:
            user["name"] = email.split("@")[0]
        if email: user["email"] = email
        if locale: user["locale"] = locale
        if username: user["username"] = username
        callback(user)
