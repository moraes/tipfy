.. _guide.templates:

Templates
=========
This guide shows how to use Jinja2 template engine with tipfy.


Quick start
-----------
TODO


Jinja2 syntax
-------------
TODO


Custom global variables, filters and functions
----------------------------------------------
Override `jinja2` from the `Jinja2Mixin` to set custom global variables,
filters and functions:

**handlers.py**

.. code-block:: python

   from werkzeug import cached_property

   from tipfy import RequestHandler
   from tipfyext.jinja2 import Jinja2Mixin

   # Define a dictionary with global variables and functions.
   custom_globals = {
       'some_key':   'some_value',
       'my_function': my_function,
   }

   # Define a dictionary with global filters.
   custom_filters = {
       'my_filter': my_filter,
   }

   class MyHandler(RequestHandler, Jinja2Mixin):
       @cached_property
       def jinja2(self):
           return Jinja2.factory(self.app, 'jinja2', _globals=custom_globals,
               filters=custom_filters)


That's all you need. For completeness, let's see other ways to do the
same thing, so that you can extend the API if needed.

You can also define a function that is called right after the environment
is created. You do that in the configuration file. It must point to where the
function is located:

**config.py**

.. code-block:: python

   config['tipfyext.jinja2'] = {
       'after_environment_created': 'my_handlers.after_environment_created',
   }

The function takes the Jinja2 environment as parameter, and you can do whatever
you need with it:

**my_handlers.py**

.. code-block:: python

   def my_function(some_argument):
       return 'done!'

   def my_filter(some_argument):
       return 'done!'

   def after_environment_created(env):
       # Define a dictionary with global variables and functions.
       _globals = {
           'some_key':   'some_value',
           'my_function': my_function,
       }

       # Define a dictionary with global filters.
       filters = {
           'my_filter': my_filter,
       }

       env.globals.update(_globals)
       env.filters.update(filters)


Alternatively, you can extend the `Jinja2` class:

**handlers.py**

.. code-block:: python

   from tipfyext.jinja2 import Jinja2, Jinja2Mixin

   def my_function(some_argument):
       return 'done!'

   def my_filter(some_argument):
       return 'done!'

   class CustomJinja2(Jinja2):
       def __init__(self, app, _globals=None, filters=None):
           # Define a dictionary with global variables and functions.
           _globals = {
               'some_key':   'some_value',
               'my_function': my_function,
           }

           # Define a dictionary with global filters.
           filters = {
               'my_filter': my_filter,
           }

           super(CustomJinja2, self).__init__(app, _globals=_globals,
               filters=filters)

Then either extend `Jinja2Mixin`, or set the `jinja2_class` to the custom one
in the handler that uses `Jinja2Mixin`:

**handlers.py**

.. code-block:: python

   from tipfyext.jinja2 import Jinja2, Jinja2Mixin

   class CustomJinja2Mixin(Jinja2Mixin):
       # The Jinja2 creator.
       jinja2_class = CustomJinja2
