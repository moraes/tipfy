.. _tipfy.ext.session-module:

tipfy.ext.session
=================
This module provides sessions using secure cookies or the datastore.



.. module:: tipfy.ext.session


Default configuration
---------------------
.. autodata:: default_config


Secure cookie functions
-----------------------
.. autofunction:: tipfy.ext.session.get_secure_cookie
.. autofunction:: tipfy.ext.session.set_secure_cookie


Session setup
-------------
.. autofunction:: tipfy.ext.session.datastore.setup
.. autofunction:: tipfy.ext.session.securecookie.setup


Session classes
---------------
.. autoclass:: tipfy.ext.session.datastore.DatastoreSessionMiddleware
.. autoclass:: tipfy.ext.session.securecookie.SecureCookieSessionMiddleware
