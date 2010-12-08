.. _guide.sessions:

Sessions
========

Quick start
-----------
To use sessions, first set a 'secret_key' config key:

**config.py**

.. code-block:: python

   config['tipfy.sessions'] = {
       'secret_key': 'my very secret secret key',
   }

Then define a base RequestHandler with SessionMiddleware:

**handlers.py**

.. code-block:: python

   from tipfy import RequestHandler
   from tipfy.sessions import SessionMiddleware

   class BaseHandler(RequestHandler):
       middleware = [SessionMiddleware()]


Now, just extend the BaseHandler when you need session support:

**handlers.py**

.. code-block:: python

   class MyHandler(BaseHandler):
       def get(self, **kwargs):
           # Any value set in the session will be persisted.
           # Note: sessions are dictionary-like objects.
           self.session['foo'] = 'bar'

           return 'testing sessions'


Using multiple sessions
-----------------------
It is possible to use multiple sessions in the a request. They can use one
the same or different backends. To do so, you request a new session to the
session store:

**handlers.py**

.. code-block:: python

   class MyHandler(BaseHandler):
       def get(self, **kwargs):
           # Request a new session using the cookie name 'cart' and the datastore
           # backend.
           session = self.session_store.get_session('cart', backend='datastore')

           # Any value set in the session will be persisted.
           session['foo'] = 'bar'

           return 'testing multiple sessions'


Changing the default session backend
------------------------------------
By default sessions use secure cookies. To use datastore or memcache-based
sessions by default, configure the sessions module:

**config.py**

.. code-block:: python

   config['tipfy.sessions'] = {
       'secret_key': 'my very secret secret key',
       # Possible values: securecookie, datastore or memcache.
       'default_backend': 'datastore',
   }


Using flash messages
--------------------
Flash messages are part of a session. They are deleted when read. To set or
read flash messages:

**handlers.py**

.. code-block:: python

   class MyHandler(BaseHandler):
       def get(self, **kwargs):
           # Add a flash message.
           self.session.add_flash('I am a flash message!')

           # Read previously set flash messages (this will delete them).
           flashes = self.session.get_flashes()

           return 'testing flash messages'


Setting and deleting cookies
----------------------------
Cookies are set or deleted calling methods from the Response object, but
sometimes it can be convenient to set or delete a cookie before having a
Response available. You can do it using the session store:

**handlers.py**

.. code-block:: python

   class MyHandler(BaseHandler):
       def get(self, **kwargs):
           # Set a cookie.
           self.session_store.set_cookie('key', 'value')

           # Delete a cookie.
           self.session_store.delete_cookie('another_key')

           return 'testing cookies'
