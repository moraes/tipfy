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
`Tipfy`_ uses a lightweight hook system to allow the application to be extended.
Several `Tipfy`_ extensions use these hooks to add extra features to the
application. For example:

  - :mod:`tipfy.ext.debugger` wraps the aplication by a debugger.
  - :mod:`tipfy.ext.i18n` loads locale for the current user and persists
    the locale value for subsequent requests.
  - :mod:`tipfy.ext.session` loads session data and saves it at the end of
    the request.

And so on. These hooks are optional. You only activate the ones you want to use.
If a module requires a hook to be activated, it is documented in the module's
API page, under the section `Application hooks`.

Custom extensions can make use of the hook system to plug functionality into
the application. The defined events are the following:

  - ``pos_init_app``: called after the :class:`tipfy.WSGIApplication`
    initializes. Receives the application as parameter.
  - ``pre_run_app``: called before the :class:`tipfy.WSGIApplication` instance
    is executed, on each request.
  - ``pre_init_request``: called in the start of a new request.
  - ``pre_dispatch_handler``: called before the current handler is dispatched.
  - ``pre_send_response``: called before the current response is returned by
    the :class:`tipfy.WSGIApplication`.
  - ``pre_handle_exception``: called before an exception is raised.

These events are executed if the application is configured to run them. In the
application configuration, under the module `tipfy`, you define which hooks
should be executed for each event. The debugger for example is set when the
``pre_run_app`` event occurs. To configure it, we add a hook for that event in
``config.py``:

.. code-block:: python

   config = {
       'tipfy': {
           'hooks': {
               'pre_run_app': ['tipfy.ext.debugger:set_debugger'],
               # ...
           },
       },
   }

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
