Hello, World! Tutorial
======================

.. _Tipfy: http://code.google.com/p/tipfy/
.. _Werkzeug's documentation: http://werkzeug.pocoo.org/documentation/dev/
.. _Jinja2's documentation: http://jinja.pocoo.org/2/documentation/

This tutorial demonstrates the simplest `Tipfy`_ application.

All that is needed to create an application using `Tipfy`_ is a class to process
requests (the "request handler") and a rule to execute the request handler when
a certain aplication URL is accessed.

First, lets create the request handler. Define a ``HelloWorldHandler`` to
display a 'Hello, World!' message, like this:

**hello.py**

.. code-block:: python

   from tipfy import RequestHandler, response

   class HelloWorldHandler(RequestHandler):
       def get(self, **kwargs):
           response.data = 'Hello, World!'
           return response

Here we extend the base class ``RequestHandler`` and add a method ``get`` to be
executed on ``GET`` requests. Then we set the response data to display our
Hello, World! message, and return the response. The key points are:

- The handler method that is called corresponds to the current request method.
  In this case we will only handle ``GET`` requests, so we only defined
  ``get()`` in the handler. To handle ``POST`` requests, we would need to add a
  ``post()`` method, and so on.

- The handler always returns a response object: ``tipfy.response`` is an empty
  ``werkzeug.Response`` object created on each request and ready to be
  filled by the application.

- ``RequestHandler`` methods receive keyword arguments from the routing system.

.. note::
   Three special variables are available to be imported from tipfy on each
   request: ``app`` (the current ``tipfy.WSGIApplication`` object), ``request``
   (the ``werkzeug.Request`` object for the current request) and ``response``
   (an empty ``werkzeug.Response`` object ready to be filled by the
   application). They also can be accessed as ``local.app``, ``local.request``
   and ``local.response``. The shorter versions are just proxies to the
   ``local`` attributes.

To execute our ``HelloWorldHandler``, we define a rule in ``urls.py``:

**urls.py**

.. code-block:: python

   from tipfy import Rule

   def get_rules():
       return [
           Rule('/', endpoint='home', handler='hello:HelloWorldHandler'),
       ]

A list of ``tipfy.Rule`` is defined in this file and returned by
``get_rules()``. The key points are:

- The first parameter in each rule is the URL path: when accessing this URL path,
  `Tipfy`_ will execute the handler defined in the rule.

- The ``endpoint`` argument is a friendly name we can use later to build url's.

- The ``handler`` argument defines which ``RequestHandler`` object will be
  executed when the defined path is accessed. In this case, we will execute
  ``HelloWorldHandler`` from ``hello.py``, so it is set to
  ``hello:HelloWorldHandler``. The handler class is imported dynamically and
  cached to be reused in subsequent requests; that's why it it is set as a
  string.

For more information about the Request and Response objects and how to define
url rules, see `Werkzeug's documentation`_.


Hello, World!, take 2: A Template Odissey
-----------------------------------------
How about using templates? Let's remake our ``HelloWorldHandler`` to use a
Jinja2 template instead of setting a raw response. First, define a
``hello.html`` template in the ``/templates`` dir:

**templates/hello.html**

.. code-block:: html+django

   {{ message }}

This template only outputs a message variable, as you see. Now let's redefine
our ``HelloWorldHandler``:

**hello.py**

.. code-block:: python

   from tipfy import RequestHandler
   from tipfy.ext.jinja2 import render_response

   class HelloWorldHandler(RequestHandler):
       def get(self, **kwargs):
           context = {'message': 'Hello, World!'}
           return render_response('hello.html', **context)

That's it. ``render_response()`` will render a Jinja2 template and fill a
response object, which is exactly what we need to return. You could also use
``tipfy.ext.mako`` if you prefer Mako templates, or create a new extension for
your favorite template engine.

Most of the time when rendering a page we just return ``render_response()``,
passing the template name and a group of keyword arguments we want to use as
variables in the template. By convention, we call these keyword arguments
``context``.

For more information about Jinja2 syntax, check `Jinja2's documentation`_.


Hello, World!, take 3: JSON Christ Superstar
--------------------------------------------

We can also easily render a ``JSON`` response with some variables, as in this
example:

**hello.py**

.. code-block:: python

   from tipfy import RequestHandler, render_json_response

   class HelloWorldHandler(RequestHandler):
       def get(self, **kwargs):
           context = {'message': 'Hello, World!'}
           return render_json_response(context)

This will output a ``application/json`` response with the context dictionary
encoded as ``JSON``.

Hello, World!, take 4: The AJAX Revenge
---------------------------------------
Another interesting thing we could do is to render a response conditionally to
the request. For example, render a template for normal requests or a ``JSON``
response for ``AJAX`` requests. Here's how we can achieve this:

**hello.py**

.. code-block:: python

   from tipfy import RequestHandler, request, render_json_response
   from tipfy.ext.jinja2 import render_response

   class HelloWorldHandler(RequestHandler):
       def get(self, **kwargs):
           context = {'message': 'Hello, World!'}
           if request.is_xhr:
               return render_json_response(context)
           else:
               return render_response('hello.html', **context)

We just need to check the ``is_xhr`` variable in the request object, which is
``True`` when the request is made through ``XMLHttpRequest``, aka ``AJAX``.
