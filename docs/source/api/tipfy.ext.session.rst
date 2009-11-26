tipfy.ext.session
=================

This module provides sessions using secure cookies or the datastore.

.. note::
   The session implementations are still pretty new and untested.
   Consider this as a work in progress.

.. module:: tipfy.ext.session


Default Configuration
---------------------
.. autodata:: default_config


Middlewares
-----------
.. autoclass:: SecureCookieSessionMiddleware
.. autoclass:: DatastoreSessionMiddleware
