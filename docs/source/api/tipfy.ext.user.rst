tipfy.ext.user
==============
This module provides an unified user authentication system that supports a
variety of backends. For now, only Google accounts is used, but adapters for
OpenID and own accounts are planned.

The interface is similar to the one provided by ``google.appengine.api.users``,
with functions like :func:`get_current_user`, :func:`create_login_url`, and
some extra ones.

The functions authenticate the user using the configured backend. The default
backend uses Google acccounts for authentication.

The current logged in user always has a record in datastore, no matter which
backend is being used. After first log in, the user is redirected to create an
account.

Appropriate handlers for signup, log in and log out must be set for this
extension, depending on the auth method used.

.. module:: tipfy.ext.user


Default configuration
---------------------
.. autodata:: default_config


Setup
-----
.. autofunction:: setup


Functions
---------
.. autofunction:: get_auth_system
.. autofunction:: create_signup_url
.. autofunction:: create_login_url
.. autofunction:: create_logout_url
.. autofunction:: get_current_user
.. autofunction:: is_current_user_admin
.. autofunction:: is_logged_in
.. autofunction:: login_required
.. autofunction:: user_required
.. autofunction:: admin_required

