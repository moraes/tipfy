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
plug new authentication methods into the user system.

Independently of the chosen method, `Tipfy`_ will require the authenticated
user to create an account in the site, so that an ``User`` entity is saved in the
datastore and becomes available for the application to reference existing users.
`Tipfy`_ provides a default user model in :class:`tipfy.ext.user.model.User`,
but you can configure it to use a custom model if needed.

In this tutorial, we will see what is needed to implement each of the
authentication systems listed above. Create a new App Engine project with
`Tipfy`_ files in it, and let's start!


Authentication with App Engine's users API
------------------------------------------
This is the default authentication method, and also the simplest to
implement: you only need to create a request handler for logged in users to
save an account. Let's do it.

The first step is to enable the user extension. After this, `Tipfy`_ will check
for logged in users on each request, and load the correspondent user entity.
All you need is to add ``tipfy.ext.user`` to the list of extensions in
``config.py``:

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
"login" or "logout" handlers, as this is done by App Engine.

In the "signup" handler, we will simply ask for users to choose an unique
username an provide an email address. You could extend the user model and add
more fields to the form; we are just sticking to the basics. So, here we create
our signup form:

**handler.py**

.. code-block:: python

   foo = {}


This handler requires a template in ``templates/users/signup.html``. Here's how
it looks like:


**signup.html**

.. code-block:: html

   <html></html>


That's it! Now we can handle signup requests properly, and save new users to
datastore.

We still need to define an URL to handle signup requests. We do this in
``urls.py``. Our URL endpoint must be ``users/signup``, as this is the default
used by the user system. Here's how we define the URL rule:


**urls.py**

.. code-block:: python

   foo = {}


Done! Now our app will know that it needs to serve the ``SignupHandler`` when
the URL ``accounts/signup`` is accessed. To see it in action, create a simple
"home" handler to link to login and logout as needed. Add our ``HomeHandler``
to ``handler.py``:

**handler.py**

.. code-block:: python

   foo = {}


Also add a simple template for our home in ``templates/home.html``:

**home.html**

.. code-block:: html

   <html></html>


And finally add an URL rule for the ``HomeHandler`` in ``urls.py``:

**urls.py**

.. code-block:: python

   foo = {}


Now let's open ``config.py`` one more time and tell `Tipfy`_ to load our users
app. `Tipfy`_ will then automatically load the URLs we defined. Here's how it
should look like:

**config.py**

.. code-block:: python

   config = {}

   config['tipfy'] = {
       'extensions': [
           'tipfy.ext.user',
       ],
       'apps_installed': [
            'apps.users',
        ],
   }


Now, start the dev server pointing to the app dir:

.. code-block:: text

   dev_appserver.py /path/to/app/dir


And then access the app in a browser:

.. code-block:: text

   http://localhost:8080/


That's it!


Authentication with "own" users
-------------------------------
Coming soon!


Authentication with OpenId, OAuth and Facebook
----------------------------------------------
Coming soon!
