tipfy.ext.messages
==================
This module provides an unified container for application status messages such
as form results, flashes, alerts and so on.

.. module:: tipfy.ext.messages


Default configuration
---------------------
.. autodata:: default_config


Setup
-----
.. autofunction:: setup


Messages container
------------------
.. autoclass:: Messages
   :members: __init__, add, add_form_error, set_flash


Functions
---------
.. autofunction:: get_flash
.. autofunction:: set_flash
