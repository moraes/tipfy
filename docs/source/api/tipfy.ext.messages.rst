.. _tipfy.ext.messages-module:

tipfy.ext.messages
==================
This module provides an unified container for application status messages such
as form results, flashes, alerts and so on.

Additionally, it provides helper functions to set and retrieve "flash" messages
in applications.

.. module:: tipfy.ext.messages


Default configuration
---------------------
.. autodata:: default_config


Flash functions
---------------
.. autofunction:: get_flash
.. autofunction:: set_flash


Messages container
------------------
.. autoclass:: Messages
   :members: __init__, add, add_form_error, set_flash
