tipfy
=====
.. _Tipfy: http://code.google.com/p/tipfy/
.. _app.yaml documentation: http://code.google.com/appengine/docs/python/config/appconfig.html

.. module:: tipfy

.. toctree::
   :maxdepth: 5

This is the main module for the WSGI application and base utilities. It provides
the base :class:`RequestHandler`, a system to hook middlewares and load
module configurations, and several other utilities.


``app.yaml``, ``main.py``, ``config.py`` and ``urls.py``
--------------------------------------------------------
These are the basic files used to configure and initialize your application.
In a common case, you'll set ``app.yaml`` and ``main.py`` once (or use the
provided ones, as they cover common uses), and specify ``config.py`` and
``urls.py`` to fit your application needs. We'll explain each one in details.


``app.yaml`` and ``main.py``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
`Tipfy`_ comes with simple ``app.yaml`` and ``main.py`` files ready to be used
by any application. Unless you have uncommon needs, you can use them as they
are.

``app.yaml`` is a configuration file required by App Engine (read more about it
in `app.yaml documentation`_), and ``main.py`` is used as the application
"bootstrap": a file that will receive requests and execute the appropriate
application handlers.

You can set a similar bootstrap in a different file, or even have multiple
bootstrap files. The important part is to map each bootstrap file in
``app.yaml``. In a simple (and common) approach, we map all requests to
``main.py``, as in this example:

**app.yaml**

.. code-block:: yaml

   application: my-app
   version: 1
   runtime: python
   api_version: 1

   handlers:
   - url: /.*
     script: main.py


``config.py``
~~~~~~~~~~~~~
By default, ``main.py`` will load configuration options from ``config.py``, to
pass the configuration dictionary to :func:`make_wsgi_app`.


``urls.py``
~~~~~~~~~~~


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
.. autofunction:: make_wsgi_app
.. autofunction:: run_wsgi_app
