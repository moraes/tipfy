tipfy.ext.session
=================
This module provides sessions using secure cookies or the datastore.

.. note::
   The session implementations are still pretty new and untested.
   Consider this as a work in progress.

.. module:: tipfy.ext.session


Default configuration
---------------------
.. autodata:: default_config


Application hooks
-----------------
.. autofunction:: set_datastore_session
.. autofunction:: set_securecookie_session


Classes
-------
.. autoclass:: DatastoreSessionMiddleware
.. autoclass:: SecureCookieSessionMiddleware
