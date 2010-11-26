.. _api.tipfy.sessions:

Sessions
========
.. module:: tipfy.sessions


Default configuration
---------------------
.. autodata:: default_config


Middleware
----------
.. autoclass:: SessionMiddleware
   :members: after_dispatch


Session Store
-------------
.. autoclass:: SessionStore
   :members: default_backends, __init__, secure_cookie_store, get_session,
             set_session, get_secure_cookie, set_secure_cookie, set_cookie,
             unset_cookie, delete_cookie, save, get_cookie_args

.. autoclass:: SecureCookieStore
   :members: __init__, get_cookie, set_cookie, get_signed_value


Session Object
--------------
.. autoclass:: BaseSession
   :members: get_flashes, add_flash

.. autoclass:: SecureCookieSession


App Engine sessions
-------------------
.. module:: tipfy.appengine.sessions

.. autoclass:: DatastoreSession
.. autoclass:: MemcacheSession


.. _Tornado: http://www.tornadoweb.org/
