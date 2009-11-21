tipfy.ext.sessions
==================
.. module:: tipfy.ext.sessions

.. toctree::
   :maxdepth: 5

This module provides sessions using secure cookies or the datastore.

.. note::
   The session implementations are still pretty new and untested.
   Consider this as a work in progress.


Middlewares
-----------
.. autoclass:: SecureCookieSessionMiddleware
.. autoclass:: DatastoreSessionMiddleware
