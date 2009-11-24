tipfy
=====
.. _Tipfy: http://code.google.com/p/tipfy/

.. module:: tipfy

.. toctree::
   :maxdepth: 5


Configuration
-------------
.. autodata:: default_config


Event hooks
-----------
.. autoclass:: EventManager
   :members: __init__, subscribe, subscribe_multi, iter, notify
.. autoclass:: EventHandler
   :members: __init__, __call__


Functions
---------
.. autofunction:: get_config
.. autofunction:: url_for
.. autofunction:: redirect
.. autofunction:: redirect_to
.. autofunction:: render_json_response
