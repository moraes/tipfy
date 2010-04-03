.. _api.tipfy:

tipfy
=====
This is the main module for the WSGI application and base utilities. It provides
the base :class:`RequestHandler`, a system to hook middlewares and load
module configurations, and several other utilities.

.. module:: tipfy


Default configuration
---------------------
.. autodata:: default_config


WSGI application and base request handler
-----------------------------------------
.. autoclass:: WSGIApplication
   :members: __init__
.. autoclass:: RequestHandler
   :members: middleware, dispatch


Configuration class
-------------------
.. autoclass:: Config
   :members: update, setdefault, get


URL Routing
-----------
.. autoclass:: Rule


Functions
---------
.. autofunction:: get_config
.. autofunction:: url_for
.. autofunction:: redirect
.. autofunction:: redirect_to
.. autofunction:: render_json_response
.. autofunction:: make_wsgi_app
.. autofunction:: run_wsgi_app


.. _Tipfy: http://code.google.com/p/tipfy/
