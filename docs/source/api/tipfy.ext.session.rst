.. _api.tipfy.ext.session:

tipfy.ext.session
=================
This module provides sessions using secure cookies or the datastore. It also
offers signed flash messages and signed cookies in general.

See in `Sessions Tutorial <http://www.tipfy.org/wiki/tutorials/sessions/>`_
a overview of session usage.


.. module:: tipfy.ext.session


Default configuration
---------------------
.. autodata:: default_config


Middleware
----------
.. autoclass:: SessionMiddleware


Mixins
------
.. autoclass:: SessionMixin
   :members: session, get_session

.. autoclass:: FlashMixin
   :members: get_flash, set_flash

.. autoclass:: MessagesMixin
   :members: messages, set_message

.. autoclass:: CookieMixin
    :members: set_cookie, delete_cookie

.. autoclass:: SecureCookieMixin
    :members: get_secure_cookie

.. autoclass:: AllSessionMixins


Session Store
-------------
.. autoclass:: SessionStore
   :members: get_session,
             get_secure_cookie, load_secure_cookie, create_secure_cookie,
             get_flash, set_flash,
             set_cookie, delete_cookie

