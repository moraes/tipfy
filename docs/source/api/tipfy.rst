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
   :members: dispatch


Application hook system
-----------------------
.. autoclass:: HookHandler
   :members: __init__, add, add_multi, iter, call
.. autoclass:: LazyHook
   :members: __init__, __call__


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
