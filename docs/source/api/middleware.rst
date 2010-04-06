Middleware
==========

WSGIApplication middleware
--------------------------
These middleware affect the whole application and are executed on every request.
They can be used to wrap the application after it is instantiated or right
before each request starts, or to handle all raised exceptions. Also they can
execute tasks before and after a ``RequestHandler`` is called.

Examples of WSGIApplication middleware:

- ``tipfy.ext.appstats.AppstatsMiddleware`` wraps the application on each
  request to record
  `appstats <http://code.google.com/appengine/docs/python/tools/appstats.html>`_
  data.

- ``tipfy.ext.debugger.DebuggerMiddleware`` also wraps the application to
  provide a helpful
  `debugger <http://werkzeug.pocoo.org/documentation/0.6/debug.html>`_ when in
  development mode.

- ``tipfy.ext.i18n.I18nMiddleware`` initializes internationalization on each
  request and persists the selected locale at the end of request.

...and many more.


Setup
~~~~~
WSGIApplication middleware are defined in the configuration file. You simply
set a list with all the middleware classes to be loaded. The classes can
be defined as strings:

**config.py**

.. code-block:: python

   config = {}

   config['tipfy'] = {
       'middleware': [
           'tipfy.ext.appstats.AppstatsMiddleware',
           'tipfy.ext.debugger.DebuggerMiddleware',
           # ...
       ],
   }


Methods
~~~~~~~
To create a WSGIApplication middleware, define a class that implements one or
more of the following methods:

(TODO)

- ``post_make_app(app)``
- ``pre_run_app(app)``
- ``pre_dispatch_handler()``
- ``post_dispatch_handler(response)``
- ``handle_exception(exception)``


RequestHandler middleware
-------------------------
(TODO)


Setup
~~~~~
RequestHandler middleware are defined in the handler classes. You simply set a
list with all the middleware classes to be loaded for that handler.

In general it is a good ided to set a base handler with all middleware used by
a group of handlers, then extend that base class (otherwise you'd have to
define the middleware for all classes, which could become a little boring after
a while).


Here's a base handler that uses sessions:


.. code-block:: python

   from tipfy import RequestHandler
   from tipfy.ext import session

   class BaseHandler(RequestHandler):
       middleware = [session.SessionMiddleware]

       def get(self, **kwargs):
           # ...


Methods
~~~~~~~
To create a RequestHandler middleware, define a class that implements one or
more of the following methods:

(TODO)

- ``pre_dispatch()``: called before the handler method for the current request
  (for example, ``get()`` or ``post()``) is executed. If a response is returned,
  no other ``pre_dispatch()`` methods from other middleware are executed. Also
  the handler method is not executed at all and that response is used instead.
  If the return value is ``None``, other middleware and the handler method are
  executed normally.

- ``post_dispatch(response)``: called after the handler method for the current
  request is executed (or a response is returned in ``pre_dispatch()``). This
  method must always return a response object.

- ``handle_exception(exception, handler=handler)``: called if an exception
  occurs when the handler method for the current request is being executed.
