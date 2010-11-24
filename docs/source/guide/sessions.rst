.. _guide.sessions:

Sessions
========

Quick start
-----------
To use sessions:

- Set 'secret_key' config key:

**config.py**

.. code-block:: python

   config['tipfy.sessions'] = {
       'secret_key': 'my very secret secret key',
   }

- Define a base RequestHandler with SessionMiddleware:

**handlers.py**

.. code-block:: python

   from tipfy import RequestHandler
   from tipfy.sessions import SessionMiddleware

   class BaseHandler(RequestHandler):
       middleware = [SessionMiddleware()]


- Extend the BaseHandler when you need session support:

**handlers.py**

.. code-block:: python

   class MyHandler(BaseHandler):
       def get(self, **kwargs):
           # Any value set in the session will be persisted.
           # Note: sessions are dictionary-like objects.
           self.session['foo'] = 'bar'

           return 'testing sessions'


Changing the session backend
----------------------------
By default sessions use secure cookies. To use datastore or memcache-based
sessions, configure the sessions module:

**config.py**

.. code-block:: python

   config['tipfy.sessions'] = {
       'secret_key': 'my very secret secret key',
       # Possible values: securecookie, datastore or memcache.
       'default_backend': 'datastore',
   }


Flash messages
--------------
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

           return 'testing flah messages'
