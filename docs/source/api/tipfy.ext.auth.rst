.. _api.tipfy.ext.auth:

tipfy.ext.auth
==============

.. _OAuth: http://oauth.net/
.. _OpenId: http://openid.net/
.. _App Engine's standard users API: http://code.google.com/appengine/docs/python/users/

This module provides an unified user accounts system that supports a
variety of authentication methods:

- Datastore ("own" users)
- `OpenId`_ (Google, Yahoo etc)
- `OAuth`_ (Google, Twitter, FriendFeed etc)
- Facebook
- `App Engine's standard users API`_

The interface is similar to the one provided by ``google.appengine.api.users``,
with functions like :func:`get_current_user`, :func:`create_login_url`, and so
on.

When this extension is enabled, users are authenticated on each request using
the configured auth system. By default, it uses App Engine's standard users API
for authentication.

Logged in users are redirected to create an account on first login. All logged
in users have a record in datastore, no matter which authentication method is
being used.

Appropriate handlers for signup, login and logout must be set for this
extension, depending on the auth method in use.

.. note::
   For examples on how to use this module, see the :ref:`tutorial.auth`.


.. module:: tipfy.ext.auth


Default configuration
---------------------
.. autodata:: default_config


Functions
---------
.. autofunction:: get_auth_system
.. autofunction:: create_signup_url
.. autofunction:: create_login_url
.. autofunction:: create_logout_url
.. autofunction:: get_current_user
.. autofunction:: is_current_user_admin
.. autofunction:: is_authenticated
.. autofunction:: login_required
.. autofunction:: user_required
.. autofunction:: admin_required
.. autofunction:: basic_auth_required
