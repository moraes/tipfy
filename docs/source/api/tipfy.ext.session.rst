tipfy.ext.session
=================
.. module:: tipfy.ext.session

.. toctree::
   :maxdepth: 5

This module provides sessions using secure cookies or the datastore.

.. note::
   The session implementations are still pretty new and untested.
   Consider this as a work in progress.


Configuration
-------------
.. autodata:: config


Middlewares
-----------
.. autoclass:: SecureCookieSessionMiddleware
.. autoclass:: DatastoreSessionMiddleware
