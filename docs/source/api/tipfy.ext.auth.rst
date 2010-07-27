.. _api.tipfy.ext.auth:

tipfy.ext.auth
==============

See the `extension wiki page <http://www.tipfy.org/wiki/extensions/auth/>`_.

.. module:: tipfy.ext.auth


Default configuration
---------------------
.. autodata:: default_config


Auth Mixins
-----------
.. autoclass:: AppEngineAuthMixin
   :members: auth_session, auth_current_user, auth_is_admin, auth_user_model,
             auth_login_url, auth_logout_url, auth_signup_url, auth_create_user,
             auth_get_user_entity

.. autoclass:: MultiAuthMixin
   :members: auth_session, auth_current_user, auth_is_admin, auth_user_model,
             auth_login_url, auth_logout_url, auth_signup_url, auth_create_user,
             auth_get_user_entity, auth_login_with_form, auth_login_with_third_party,
             auth_set_session, auth_logout

Decorators
----------
.. autofunction:: login_required
.. autofunction:: user_required
.. autofunction:: admin_required


Middleware
----------
.. autoclass:: LoginRequiredMiddleware
.. autoclass:: UserRequiredMiddleware
.. autoclass:: AdminRequiredMiddleware


User model
----------
.. module:: tipfy.ext.auth.model

.. autoclass:: User
   :members: get_by_username, get_by_auth_id, create, set_password,
             check_password, check_session
