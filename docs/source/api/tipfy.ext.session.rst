tipfy.ext.session
=================
This module provides sessions using secure cookies or the datastore.

.. note::
   The session implementations are still pretty new and untested.
   Consider this as a work in progress.

.. module:: tipfy.ext.session


Default configuration
---------------------
.. autodata:: default_config


Application hooks
-----------------
.. autofunction:: set_datastore_session
.. autofunction:: set_securecookie_session


Classes
-------
.. autoclass:: DatastoreSessionMiddleware
.. autoclass:: SecureCookieSessionMiddleware


How to use sessions
-------------------
First, setup an application hook in ``config.py`` to initialize the session
middleware. See in :func:`set_datastore_session` or
:func:`set_securecookie_session` how to do this.

After the hook is set, session will be available on each request. You can
import and use it like a dictionary. A simple example:

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


.. _Tipfy: http://code.google.com/p/tipfy/
