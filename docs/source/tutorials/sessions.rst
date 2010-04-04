.. _tutorial.sessions:

Sessions Tutorial
=================

.. _Tipfy: http://code.google.com/p/tipfy/

`Tipfy`_ provides sessions using secure cookies or the datastore. In this
tutorial, we will have an overview of the :ref:`api.tipfy.ext.session`
module and learn how to use sessions.

Overview
--------
Sessions in `Tipfy`_ use secure cookies to store the session data (for
securecookie-based sessions) or the session id (for datastore-based sessions).
Secure cookies are cookies that are not alterable from the client side because
they add a checksum that is validated in the server when read.

For securecookie-based sessions, this means that all the session data is stored
in the cookie, so it is still readable from the client as a normal cookie is.
The data can't be altered, however, because the checksum will fail if someone
tries to forge a cookie. This approach saves resources avoiding datastore hits
while keeping the data safe from forgery attempts.

For datastore-based sessions, the data is saved in datastore and the secure
cookie only stores a random session id that references the session entity. This
adds a little overhead as an entity is saved each time the session data changes,
but it may be appropriate if you don't want to expose the data stored in
the session.

.. note::
   All sessions in `Tipfy`_ are lazy: session values are only loaded when
   accessed, and only saved if they change.

   `Tipfy`_ also tries to minimize the overhead of datastore-based sessions
   storing and reading the session data from memcache. Still, you should only
   use datastore-based session if you really need it.

   On the other hand, cookie-based sessions are very lightweight but the amount
   of data you can store in a cookie is limited.


Configuration
-------------
To start, we need to configure a secret key that will be used to generate an
``HMAC`` for the session cookies. Choose a strong, random secret key to ensure
it can't be compromised. Then set it in ``config.py``:

**config.py**

.. code-block:: python

   config = {}

   config['tipfy.ext.session'] = {
       'secret_key': 'my_strong_secret_key',
   }


This is the only required configuration, but there are other options that you
may want to change. All config options are listed in
:ref:`api.tipfy.ext.session` documentation.

That's all! Now we can start using sessions in our handlers.


Using sessions
--------------
All handlers that need to use sessions should add a ``SessionMiddleware`` to
the list of middleware defined in the handler class.

The middleware will add a ``session_store`` attribute to ``local``, which is an
instance of ``tipfy.ext.session.SessionStore``, and will ensure that the
session data is saved at the end of the request. You can request the current
session from the session store:

**handlers.py**

.. code-block:: python

   from tipfy import local, RequestHandler, Response
   from tipfy.ext.session import SessionMiddleware

   class MyHandler(RequestHandler):
       # This list enables middleware for the handler.
       middleware = [SessionMiddleware]

       def get(self, **kwargs):
           session = local.session_store.get_session()
           session['foo'] = 'bar'

           # [...]


To make this more convenient, you can use a ``SessionMixin`` that sets
``session`` as an attribute of the handler, so you can access it directly:

**handlers.py**

.. code-block:: python

   from tipfy import RequestHandler, Response
   from tipfy.ext.session import SessionMiddleware, SessionMixin

   class MyHandler(RequestHandler, SessionMixin):
       # This list enables middleware for the handler.
       middleware = [SessionMiddleware]

       def get(self, **kwargs):
           self.session['foo'] = 'bar'

           # [...]


.. note::
   A session is a dictionary-like object. You can use all dictionary methods to
   get, set, update and delete keys.


Let's see a simple example of a session being read and set:

**handlers.py**

.. code-block:: python

   from tipfy import request, RequestHandler, Response, url_for
   from tipfy.ext.session import SessionMiddleware, SessionMixin


   class BasicSessionHandler(RequestHandler, SessionMixin):
       """A very basic session example."""
       # This list enables middleware for the handler.
       middleware = [SessionMiddleware]

       def get(self, **kwargs):
           # Check if a key is set in session.
           value = self.session.get('foo', None)
           if value:
               # Add the session value to our response.
               html = 'Session has a value stored for "foo": %s' % value
               html += '<br><a href="%s">Delete the session</a>' % url_for(
                   'sessions/delete', redirect=request.url)
           else:
               html = 'Session was not set!'
               # Set a value in the session, like in a dictionary.
               self.session['foo'] = 'bar'

           return Response(html, mimetype='text/html')


When you first access this handler, the response will be empty. But on the
second time it'll present the value of the saved session. It will also show
a link to delete the session... we will implement this later.


The Awfully Simple Shopping Cart
--------------------------------
Here's another example. Let's create a very very simple "shopping cart":

**handlers.py**

.. code-block:: python

   from tipfy import request, RequestHandler, Response, url_for
   from tipfy.ext.session import SessionMiddleware, SessionMixin


   class ShoppingCartHandler(RequestHandler, SessionMixin):
       # This list enables middleware for the handler.
       middleware = [SessionMiddleware]

       def get(self, **kwargs):
           # Add product to session if a 'add-product' is in GET.
           to_add = request.args.get('add-product', None)
           if to_add is not None:
               self.session.setdefault('products', []).append(to_add)

           # Remove product from session if a 'remove-product' is in GET.
           to_remove = request.args.get('remove-product', None)
           if to_remove is not None:
               self.session.setdefault('products', [])
               try:
                   index = self.session['products'].index(to_remove)
                   self.session['products'].pop(index)
               except ValueError:
                   # Name wasn't in the list.
                   pass

           # Get products from session.
           products = self.session.get('products', None)

           if products:
               html = 'Products in cart: ' + ', '.join(products)
               html += '<br><a href="%s">Clear the cart</a>' % url_for(
                   'sessions/delete', redirect=url_for('sessions/cart'))
           else:
               html = 'The cart is empty.'

           return Response(html, mimetype='text/html')


In the code above, a product is added to a products list whenever you access an
URL with `add-product` or `remove-product` in the GET parameters.

Let's test it. First we should add some URL rules for the handlers above:

**urls.py**

.. code-block:: python

   from tipfy import Rule

   def get_rules():
       rules = [
           Rule('/', endpoint='home', handler='handlers.BasicSessionHandler'),
           Rule('/cart', endpoint='sessions/cart', handler='handlers.ShoppingCartHandler'),
           Rule('/delete-session', endpoint='sessions/delete', handler='handlers.DeleteSessionHandler'),
       ]

       return rules


Now access the URLs:

.. code-block:: text

   http://localhost:8080/cart
   http://localhost:8080/cart?add-product=foo
   http://localhost:8080/cart?add-product=bar
   http://localhost:8080/cart?add-product=baz
   http://localhost:8080/cart?remove-product=foo
   http://localhost:8080/cart?remove-product=bar
   http://localhost:8080/cart?remove-product=baz


Accessing each of the URLs above, our shopping cart will be updated and stored
in the session.


Deleting sessions
-----------------
To delete a session, you can simply call ``session.clear()``, as a session is a
dictionary-like object. However, this means that the session cookie will still
be stored, even if empty. To remove the session also deleting the session
cookie, you must call the appropriate ``delete_session()`` method fom the
``SessionStore``:

.. code-block:: python

   from tipfy import local, redirect, request, RequestHandler, Response, url_for
   from tipfy.ext.session import SessionMiddleware, SessionMixin

   class DeleteSessionHandler(RequestHandler, SessionMixin):
       """A handler that deletes current session and redirects back."""
       # This list enables middleware for the handler.
       middleware = [SessionMiddleware]

       def get(self, **kwargs):
           # Delete the current session.
           # You can also call self.session.clear() to make it empty instead
           # of deleting the cookie.
           local.session_store.delete_session()

           # Redirect back.
           return redirect(request.args.get('redirect', url_for('home')))


That's it. Now the basic session and the shopping cart examples above can also
delete their sessions.


Here we had an overview of :ref:`api.tipfy.ext.session`. There are other things
to explore in the session store, such as flash messages and secure cookie
generation, but that is up to you. Take a look at the API and have fun!
