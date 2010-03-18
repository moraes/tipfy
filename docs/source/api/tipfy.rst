.. _tipfy-module:

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


Extensions
----------
`Tipfy`_ uses a lightweight hook system to allow the application to be extended.
Several `Tipfy`_ extensions use these hooks to add extra features to the
application. For example:

  - :mod:`tipfy.ext.debugger` wraps the aplication by a debugger.
  - :mod:`tipfy.ext.i18n` loads locale for the current user and persists
    the locale value for subsequent requests.
  - :mod:`tipfy.ext.session` loads session data and saves it at the end of
    the request.

And so on. These extensions are all optional. You only activate the ones you
want to use. If an extension requires any setup, it is documented in the
module's API page, under the section `Setup`.

Setting up an extension is simple: in the application configuration, under the
module `tipfy`, you define which extensions you want to enable. For example,
to enable the debugger and internationalization:

**config.py**

.. code-block:: python

   config = {
       'tipfy': {
           # Extensions plug into the application.
           # Here we enable debugger and internalization ones.
           'extensions': [
               'tipfy.ext.debugger',
               'tipfy.ext.i18n',
            ],
       },
   }


When the app is initialized, all configured extension modules are loaded and
a ``setup()`` function is executed. You can create your own extensions and just
add to your custom extension module to the configuration. The only requirement
is that the module must have a ``setup()`` function.

Hooks
-----
Custom extensions can make use of the hook system to plug functionality into
the application. The defined events are the following:

  - ``pre_run_app(app)``: called before the :class:`tipfy.WSGIApplication`
    instance is called, on each request.
  - ``pre_init_request(app, environ)``: called right at the beginning of a
    request.
  - ``pre_match_url(app, request)``: called right before the current URL is
    matched.
  - ``pre_dispatch_handler(app, request)``: called before the current handler
    is dispatched.
  - ``post_dispatch_handler(app, request, response)``: called after the current
    handler is dispatched.
  - ``pre_end_request(app, request, response)``: called right at the end of the
    request.
  - ``pre_handle_exception(app, request, exception)``: called before an
    exception is raised.

You can add many hooks to the same event; they will be executed in order.


Hook classes
------------
.. autoclass:: HookHandler
   :members: __init__, add, add_multi, iter, call
.. autoclass:: LazyCallable
   :members: __init__, __call__


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
