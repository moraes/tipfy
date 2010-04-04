.. _api.tipfy.ext.session:

tipfy.ext.session
=================
This module provides sessions using secure cookies or the datastore. It also
offers signed flash messages and signed cookies in general.

See in :ref:`tutorial.sessions` an overview of sessions usage.


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
   :members: session, get_flash, set_flash

.. autoclass:: MessagesMixin
   :members: messages, set_message, set_form_error


Session Store
-------------
.. autoclass:: SessionStore
   :members: get_session, delete_session, get_secure_cookie, load_secure_cookie,
             create_secure_cookie, get_flash, set_flash, set_cookie

