Sessions Tutorial
=================

.. _Tipfy: http://code.google.com/p/tipfy/

`Tipfy`_ provides sessions using secure cookies or the datastore. Once enabled,
sessions become available to the application and are persisted automatically.
In this tutorial, we will see how to use sessions in `Tipfy`_.

Also check :ref:`tipfy.ext.session-module` for a complete reference.


Configuration
-------------
To enable sessions, we need to add a session module to the list of extensions
in ``config.py``. This will initialize and persiste sessions on each request.
The options are ``tipfy.ext.session.datastore``, to save sessions in datastore,
or ``tipfy.ext.session.securecookie``, to save sessions in secure cookies.
Either way, we also need to configure a ``secret_key`` that will be used to
generate an ``HMAC`` for the session id and data:

**config.py**

.. code-block:: python

   config = {}

   config['tipfy'] = {
       'extensions': [
           'tipfy.ext.session.securecookie',
       ],
   }

   config['tipfy.ext.session'] = {
       'secret_key': 'my_secret_key',
   }


That's all! Now we can start using sessions in our handlers.

Using sessions
--------------
After the extension is set, session will be available on each request. You can
import the ``session`` variable from the extension module and use it like a
dictionary. A simple example:

**session_test.py**

.. code-block:: python

   from tipfy import RequestHandler, request, response
   from tipfy.ext.session import session

   class MyHandler(RequestHandler):
      def get(self, **kwargs):
          # Check if a key is set in session.
          if session.get('foo'):
              # Add the session value to our response.
              response.data = session.get('foo')
          else:
              response.data = 'Session was not set!'

          # Set a value in the session, like in a dictionary.
          session['foo'] = 'bar'

          return response


When you first access this handler, the response will be empty. But on the
second time it'll present the value of the saved session.

Here's another example. Let's create a very simple "shopping cart":

**session_test.py**

.. code-block:: python

   from tipfy import RequestHandler, request, response
   from tipfy.ext.session import session

   class MyHandler(RequestHandler):
      def get(self, **kwargs):
          # Add product to session if a 'add-product' is in GET.
          to_add = request.args.get('add-product', None)
          if to_add is not None:
              session.setdefault('products', []).append(to_add)

          # Remove product from session if a 'remove-product' is in GET.
          to_remove = request.args.get('remove-product', None)
          if to_remove is not None:
              session.setdefault('products', [])
              try:
                  session['products'].pop(session['products'].index(to_remove))
              except ValueError:
                  # Name wasn't in the list.
                  pass

          # Get products from session.
          products = session.get('products', None)

          if products:
              response.data = 'Products in cart: ' + ', '.join(products)
          else:
              response.data = 'The cart is empty.'

          return response


In the code above, a product is added to a products list whenever you access an
URL with `add-product` or `remove-product` in the GET parameters.

Let's test it. First add an URL for the handler above:

**urls.py**

.. code-block:: python

   from tipfy import Rule

   def get_rules():
       return [
           Rule('/session-test', endpoint='session', handler='session_test:MyHandler'),
       ]


Now access the URLs:

.. code-block:: text

   http://localhost:8080/session-test?add-product=foo
   http://localhost:8080/session-test?add-product=bar
   http://localhost:8080/session-test?add-product=baz
   http://localhost:8080/session-test?remove-product=foo
   http://localhost:8080/session-test?remove-product=bar
   http://localhost:8080/session-test?remove-product=baz


Our "cart" will be updated and the session will be persisted.

.. note::
   Any implementation of datastore based session may add significant overhead
   to an application. `Tipfy`_ tries to minimize this using memcache and
   performing writes only when the session data changes. Still, you should only
   enable datastore based session if you really need it.

   On the other hand, cookie based session is much more lightweight but the
   amount of data you can store in a cookie is limited.
