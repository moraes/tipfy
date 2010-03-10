.. _user-auth-tutorial:

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
plug new authentication methods into the user system. Check out the
:ref:`tipfy.ext.user-module` module for the API reference and configuration
options for the user system.

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


- :ref:`user-auth-gae-tutorial`
- :ref:`user-auth-own-tutorial`
- :ref:`user-auth-external-tutorial`

.. note::
   The source code for all these examples is compiled in the
   `tipfy-examples <http://code.google.com/p/tipfy-examples/source/browse/#hg/tutorials>`_
   project.


.. _user-auth-gae-tutorial:

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
   when using `Tipfy`_. There are various ways to organize an application and the
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
           error = None

           if username and email:
               # Create an unique auth id for this user.
               # For GAE auth, we use 'gae|' + the gae user id.
               auth_id = 'gae|%s' % users.get_current_user().user_id()

               # Set the properties of our user.
               kwargs = {
                   'email': email,
                   'is_admin': users.is_current_user_admin(),
               }

               # Save user to datastore.
               user = get_auth_system().create_user(username, auth_id, **kwargs)

               if user is None:
                   # If no user is returned, the username already exists.
                   error = 'Username already exists. Please choose a different one.'
               else:
                   # User was saved: redirect to the previous URL.
                   return redirect(request.args.get('redirect', '/'))

           context = {
               'current_url': request.url,
               'error': error,
           }
           return render_response('users/signup.html', **context)


This handler requires a template in ``templates/users/signup.html``. Here's how
it looks like:


**signup.html**

.. code-block:: html

   <html>
       <body>
           <h1>Please choose an username and confirm your e-mail:</h1>
           {% if error %}
               <h3>{{ error }}</h3>
           {% endif %}
           <form method="post" action="{{ current_url }}">
               <p><label for="username">Username</label>
               <input type="text" id="username" name="username"><p>

               <p><label for="email">E-mail</label>
               <input type="text" id="email" name="email"></p>

               <p><input type="submit" name="submit" value="save"></p>
           </form>
       </body>
   </html>


.. note::
   To keep things more simple and objective, we decided to not use any form
   library in this tutorial, or `Tipfy`_'s internationalization utilities.
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


.. _user-auth-own-tutorial:

Authentication with "own" users
-------------------------------
Authenticating with "own" users is not much different than using App Engine's
users API. We will only need to add handlers for login and logout, and we can
reuse the ``users`` app we made above with few small changes.

Let's start configuring auth system to ``tipfy.ext.user.MultiAuth``, instead of
the default one that uses App Engine's auth. This is also the same system used
for OpenId, OAuth, Facebook and others, but we will see this later.
Additionally, we need to provide a secret key for the sessions that will keep
users logged in. This is important.

Open ``config.py`` and change the configuration for the user and session
extensions:

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

   config['tipfy.ext.user'] = {
       'auth_system': 'tipfy.ext.user.MultiAuth',
   }

   config['tipfy.ext.session'] = {
       'secret_key': 'my very very very secret phrase',
   }


.. note::
   All modules that have configuration options list them in the session
   ``Default configuration`` in the module documentation. Take a look at the
   ones we just configured: :ref:`tipfy.ext.user-module` and
   :ref:`tipfy.ext.session-module`.


In the ``urls.py`` we created for the users app, add URL rules for login and
logout, in addition to the previous rules we have set:

**urls.py**

.. code-block:: python

   from tipfy import Rule

   def get_rules():
       rules = [
           Rule('/', endpoint='home', handler='apps.users.handlers.HomeHandler'),
           Rule('/accounts/signup', endpoint='users/signup', handler='apps.users.handlers.SignupHandler'),
           Rule('/accounts/login', endpoint='users/login', handler='apps.users.handlers.LoginHandler'),
           Rule('/accounts/logout', endpoint='users/logout', handler='apps.users.handlers.LogoutHandler'),
       ]

       return rules


The logout handler is the easiest, so let's start with it. Open ``handlers.py``
and add our ``LogoutHandler`` to the end of the file:

**handlers.py**

.. code-block:: python

   class LogoutHandler(RequestHandler):
       """Logout the user."""
       def get(self, **kwargs):
           get_auth_system().logout()
           return redirect(request.args.get('redirect', '/'))


It is that simple! It just asks the auth system to logout the current user, and
then redirects to the previous URL we have set in the GET parameters, with
fallback to redirect to the home page.

The login handler is not much harder: we just need to display a login form
and then verify an username and password. Add it to your ``handlers.py`` (and,
oh, also import ``create_signup_url`` from ``tipfy.ext.user``):

**handlers.py**

.. code-block:: python

   class LoginHandler(RequestHandler):
       def get(self, **kwargs):
           if get_current_user() is not None:
               # Don't allow existing users to access this page.
               return redirect(request.args.get('redirect', '/'))

           return self._render_response()

       def post(self, **kwargs):
           if get_current_user() is not None:
               # Don't allow existing users to access this page.
               return redirect(request.args.get('redirect', '/'))

           error = None

           # Get all posted data.
           username = request.form.get('username', '').strip()
           password = request.form.get('password', '').strip()
           remember = request.form.get('remember', '') == 'y'

           if get_auth_system().login_with_form(username, password, remember):
               # Redirect to the original URL after login.
               return redirect(request.args.get('redirect', '/'))
           else:
               error = 'Username or password invalid. Please try again.'

           return self._render_response(error=error)

       def _render_response(self, error=None):
           context = {
               'current_url': request.url,
               'signup_url': create_signup_url(request.url),
               'error': error,
           }

           return render_response('users/login.html', **context)

The function that authenticates the user is
``login_with_form(username, password, remember)``. If the username and password
are valid, the user system will recognize and persist the current user s logged
in.

If "Remember me on this computer" is checked, the user will be kept login even
if it ends the current session closing the browsing window. This is done using
secure cookies and an unique token that is renewed from time to time, to
conform with best safety practices.


The login handler uses a template that we will save in
``templates/users/login.html``. Here it is:

**home.html**

.. code-block:: html

   <html>
       <body>
           <h1>Login</h1>
           {% if error %}
               <h3>{{ error }}</h3>
           {% endif %}
           <form method="post" action="{{ current_url }}">
               <p><label for="username">Username</label>
               <input type="text" id="username" name="username"></p>

               <p><label for="password">Password</label>
               <input type="password" id="password" name="password"></p>

               <p><input type="checkbox" name="remember" value="y"> Remember me on this computer</p>

               <p><input type="submit" name="submit" value="login"></p>

               <p>Don't have an account? <a href="{{ signup_url }}">Signup here</a>.</p>
           </form>
       </body>
   </html>


One step left! Now we only need to adapt our previous signup handler to support
the user defining a password. Let's do it:

**handlers.py**

.. code-block:: python

   class SignupHandler(RequestHandler):
       def get(self, **kwargs):
           return self._render_response()

       def post(self, **kwargs):
           username = request.form.get('username').strip()
           email = request.form.get('email').strip()
           password = request.form.get('password').strip()
           confirm_password = request.form.get('confirm_password').strip()
           error = None

           if password != confirm_password:
               error = 'Passwords didn\'t match. Please try again.'
               return self._render_response(error=error)

           if username and email:
               # Create an unique auth id for this user.
               # For own auth, we use 'own|' + the username.
               auth_id = 'own|%s' % username

               # Set the properties of our user.
               kwargs = {
                   'email': email,
                   'password': password,
               }

               # Save user to datastore. If the username already exists, return
               # value will be None.
               user = get_auth_system().create_user(username, auth_id, **kwargs)

               if user is None:
                   # If no user is returned, the username already exists.
                   error = 'Username already exists. Please choose a different one.'
               else:
                   # User was saved: redirect to the previous URL.
                   return redirect(request.args.get('redirect', '/'))

           return self._render_response(error=error)

       def _render_response(self, error=None):
           context = {
               'current_url': request.url,
               'error': error,
           }
           return render_response('users/signup.html', **context)


The key here is the function ``create_user()``, which will generate a hash for
the password and save the new user to datastore.

Also adapt the template in ``templates/users/signup.html`` to add fields for
password and password confirmation:

**home.html**

.. code-block:: html

   <html>
       <body>
           <h1>Please choose an username and password and confirm your e-mail:</h1>
           {% if error %}
               <h3>{{ error }}</h3>
           {% endif %}
           <form method="post" action="{{ current_url }}">
               <p><label for="username">Username</label>
               <input type="text" id="username" name="username"><p>

               <p><label for="email">E-mail</label>
               <input type="text" id="email" name="email"></p>

               <p><label for="password">Password</label>
               <input type="password" id="password" name="password"></p>

               <p><label for="confirm_password">Confirm Password</label>
               <input type="password" id="confirm_password" name="confirm_password"></p>

               <p><input type="submit" name="submit" value="save"></p>
           </form>
       </body>
   </html>


And we are all set. We have an own users system in place, with "remember me"
feature and all that jazz. Start the dev server pointing to the app dir to
test it:

.. code-block:: text

   dev_appserver.py /path/to/app/dir


And then access the app in a browser:

.. code-block:: text

   http://localhost:8080/


Cool, uh?


.. _user-auth-external-tutorial:

Authentication with OpenId, OAuth and Facebook
----------------------------------------------
This tutorial is coming soon!
