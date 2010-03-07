User Authentication Tutorial
============================

.. _Tipfy: http://code.google.com/p/tipfy/
.. _OAuth: http://oauth.net/
.. _OpenId: http://openid.net/
.. _App Engine's standard users API: http://code.google.com/appengine/docs/python/users/

`Tipfy`_ has an unified user accounts system that supports authentication using:

- Datastore ("own" users)
- `OpenId`_ (Google, Yahoo etc)
- `OAuth`_ (Google, Twitter, FriendFeed etc)
- Facebook
- `App Engine's standard users API`_

You can choose one, all or a mix of the available authentication systems, or
implement new authentication methods to plug into the user system.

Independently of the chosen method, `Tipfy`_ will require the authenticated
user to create an account in the site, so that an `User` entity is saved in the
datastore and becomes available for the application to reference existing users.
`Tipfy`_ provides a default user model in :class:`tipfy.ext.user.model.User`,
but you can configure it to use a custom model if needed.


Authentication with App Engine's users API
------------------------------------------
This is the default authentication method, and also the simplest to
implement: no configuration is required and you only need to create a request
handler for logged in users to save an account. Let's do it.

The first step is to enable the user extension in ``config.py``. After this,
`Tipfy`_ will check for logged in users on each request, and load the
correspondent user entity. All you need is to add ``tipfy.ext.user`` to the
list of extensions:


**config.py**

.. code-block:: python

   config = {}

   config['tipfy'] = {
       'extensions': [
           'tipfy.ext.user',
       ],
   }


Now let's create an app to manage our users. In your application dir create a
directory ``apps`` and inside it, create a directory ``users``. Then create an
empty ``__init__.py`` for both directories. And finally, create empty
``urls.py`` and ``handler.py`` in the ``users`` dir. This is the skeleton for
our users app. In the end you'll have::


  /apps
    |__ /users
    |     |__ __init__.py
    |     |__ handler.py
    |     |__ urls.py
    |
    |__ __init__.py


We need a "signup" handler to save logged in users in datastore. We don't need
handlers to login or logout, as this is handled by App Engine.





Authentication with "own" users
-------------------------------
Coming soon!


Authentication with OpenId, OAuth and Facebook
----------------------------------------------
Coming soon!
