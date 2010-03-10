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
user to create an account in the site, so that an ``User`` entity is saved in
the datastore and becomes available for the application to reference existing
users. `Tipfy`_ provides a default user model in
:class:`tipfy.ext.user.model.User`, but you can configure it to use a custom
model if needed.

In this tutorial, we will see what is needed to implement each of the
authentication systems listed above. We will basically create handlers for
login, logout, and signup.

Create a new App Engine project with `Tipfy`_ files in it, and let's start!


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


.. note::
   You can find a complete list of the available configuration keys in the
   :ref:`tipfy-module` module documentation.


Now let's create an app to manage our users. In your application dir create a
directory ``apps`` and inside it, create a directory ``users``. Then create an
empty ``__init__.py`` for both directories. And finally, create empty
``urls.py`` and ``handlers.py`` in the ``users`` dir. This is the skeleton for
our users app. In the end you'll have::


  /apps
    |__ /users
    |     |__ __init__.py
    |     |__ handlers.py
    |     |__ urls.py
    |
    |__ __init__.py


.. note::
   You don't **need** to follow a specific directory structure for your apps
   when using Tipfy. There are various ways to organize an application and the
   schema above is just one that we consider convenient.


We need a "signup" handler to save logged in users in datastore. We don't need
"login" or "logout" handlers, as this is done by App Engine.

In the "signup" handler, we will simply ask for users to choose an unique
username an provide an email address. You could extend the user model and add
more fields to the form; we are just sticking to the basics. So, here we create
our signup form:

**handlers.py**

.. code-block:: python

   from google.appengine.api import users

   from tipfy import RequestHandler, request, response, redirect
   from tipfy.ext.jinja2 import render_response
   from tipfy.ext.user import create_login_url, create_logout_url, \
       get_auth_system, get_current_user


   class SignupHandler(RequestHandler):
       def get(self, **kwargs):
           context = {
               'current_url': request.url,
           }
           return render_response('users/signup.html', **context)

       def post(self, **kwargs):
           username = request.form.get('username').strip()
           email = request.form.get('email').strip()

           if username and email:
               # Create an unique auth id for this user.
               # For GAE auth, we use 'gae|' + the gae user id.
               auth_id = 'gae|%s' % users.get_current_user().user_id()

               # Set the properties of our user.
               kwargs = {
                   'email': email,
                   'is_admin': users.is_current_user_admin(),
               }

               # Save user to datastore. If the username already exists, return
               # value will be None.
               user = get_auth_system().create_user(username, auth_id, **kwargs)

               if user is not None:
                   # User was saved: redirect to the previous URL.
                   return redirect(request.args.get('redirect', '/'))

           context = {
               'current_url': request.url,
           }
           return render_response('users/signup.html', **context)


This handler requires a template in ``templates/users/signup.html``. Here's how
it looks like:


**signup.html**

.. code-block:: html

   <html>
       <body>
           <h1>Please choose an username and confirm your e-mail:</h1>
           <form method="post" action="{{ current_url }}">
               <label for="username">Username</label>
               <input type="text" id="username" name="username">

               <label for="email">E-mail</label>
               <input type="text" id="email" name="email">

               <input type="submit" name="submit" value="save">
           </form>
       </body>
   </html>


.. note::
   To keep things more simple and objective, we decided to not use any form
   library in this tutorial, or tipfy's internationalization utilities.
   Form handling and i18n may be the subject for a new tutorial. :)


That's it! Now we can handle signup requests properly, and save new users to
datastore.

We still need to define an URL to handle signup requests. We do this in
``urls.py``. Our URL endpoint must be ``users/signup``, as this is the default
used by the user system. Here's how we define the URL rule:


**urls.py**

.. code-block:: python

   from tipfy import Rule

   def get_rules():
       rules = [
           Rule('/accounts/signup', endpoint='users/signup', handler='apps.users.handlers.SignupHandler'),
       ]

       return rules


Done! Now our app will know that it needs to serve the ``SignupHandler`` when
the URL ``accounts/signup`` is accessed. To see it in action, create a simple
"home" handler to link to login and logout as needed. Add our ``HomeHandler``
to the end ``handlers.py``:

**handlers.py**

.. code-block:: python

   class HomeHandler(RequestHandler):
       def get(self, **kwargs):
           context = {
               'user':       get_current_user(),
               'login_url':  create_login_url(request.url),
               'logout_url': create_logout_url(request.url),
           }
           return render_response('home.html', **context)


Also add a simple template for our home in ``templates/home.html``:

**home.html**

.. code-block:: html

   <html>
       <body>
           {% if user %}
               <p>Logged in as {{ user.username }}. <a href="{{ logout_url }}">Logout</a></p>
           {% else %}
               <p><a href="{{ login_url }}">Login</a></p>
           {% endif %}
       </body>
   </html>


And finally add an URL rule for the ``HomeHandler`` in ``urls.py``, in addition
to the existing rule for the ``SignupHandler``:

**urls.py**

.. code-block:: python

   from tipfy import Rule

   def get_rules():
       rules = [
           Rule('/', endpoint='home', handler='apps.users.handlers.HomeHandler'),
           Rule('/accounts/signup', endpoint='users/signup', handler='apps.users.handlers.SignupHandler'),
       ]

       return rules

Time to test if it works! Open ``config.py`` one more time and tell `Tipfy`_ to
load our users app. We do this adding our ``apps.users`` to the list of
``apps_installed`` in the configuration. `Tipfy`_ will then automatically load
the URLs we defined.


Here's how our config should look like:

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
