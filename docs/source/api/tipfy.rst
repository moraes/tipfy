.. _api.tipfy:

tipfy
=====
This is the main Tipfy module. It provides a WSGI application, the base
:class:`RequestHandler` class, configuration and hook systems and several
other utilities.

.. module:: tipfy


Default configuration
---------------------
.. autodata:: default_config


WSGI application
----------------
.. autoclass:: Tipfy
   :members: __init__


RequestHandler
--------------
.. autoclass:: RequestHandler
   :members:  middleware, __init__, __call__, abort, get_config,
              handle_exception, redirect, redirect_to, url_for


Configuration class
-------------------
.. autoclass:: Config
   :members: get, get_or_load, setdefault, update


URL Routing
-----------
.. autoclass:: Rule
.. autoclass:: HandlerPrefix


Functions
---------
.. autofunction:: get_config
.. autofunction:: url_for
.. autofunction:: redirect
.. autofunction:: redirect_to
.. autofunction:: render_json_response
.. autofunction:: make_wsgi_app
.. autofunction:: run_wsgi_app
