.. module:: tipfy

tipfy
=====

This is the main module for the WSGI application and base utilities. It provides
the base :class:`RequestHandler`, a system to hook middlewares and load
module configurations, and several other utilities.


Default Configuration
---------------------
.. autodata:: default_config


Application hook system
-----------------------
.. autoclass:: EventManager
   :members: __init__, subscribe, subscribe_multi, iter, notify
.. autoclass:: EventHandler
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
