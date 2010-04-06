.. _api.tipfy.ext.appstats:

tipfy.ext.appstats
==================
This module provides a middleware to record statistics using App Engine's
appstats.

To enable Appstats, add the middleware to config:

**config.py**

.. code-block:: python

   config = {}

   config['tipfy'] = {
       'middleware': [
           'tipfy.ext.appstats.AppstatsMiddleware',
           # ...
       ],
   }


.. module:: tipfy.ext.appstats

Middleware
----------
.. autoclass:: AppstatsMiddleware
