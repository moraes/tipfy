tipfy
=====
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


Functions
---------
.. autofunction:: get_config
.. autofunction:: url_for
.. autofunction:: redirect
.. autofunction:: redirect_to
.. autofunction:: render_json_response
