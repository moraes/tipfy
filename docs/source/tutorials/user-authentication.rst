.. _tutorial.auth:

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
:ref:`api.tipfy.ext.auth` module for the API reference and configuration
options for the user system.

Independently of the chosen method, `Tipfy`_ will require the authenticated
user to create an account in the site, so that an ``User`` entity is saved in
the datastore and becomes available for the application. `Tipfy`_ provides a
default user model in :class:`tipfy.ext.auth.model.User`, but you can configure
it to use a custom model if needed.

In this tutorial, we will see what is needed to implement each of the
authentication systems listed above. We will basically configure the application
to use the chosen auth method create handlers for login, logout, and signup.

Create a new App Engine project with `Tipfy`_ files in it, and let's start!


- :ref:`user-auth-gae-tutorial`
- :ref:`user-auth-own-tutorial`
- :ref:`user-auth-external-tutorial`

.. note::
   The source code for these tutorials is available in the ``examples``
   directory or `Tipfy`_'s repository. See them
   `here <http://code.google.com/p/tipfy/source/browse/#hg/examples>`_.


.. _user-auth-gae-tutorial:

Authentication with App Engine's users API
------------------------------------------
This is the default authentication method, and also the simplest to
implement: you only need to create a request handler for logged in users to
save an account.

First let's create an app to manage our users. In your application dir create a
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


Now let's define two URL rules to use in our example: one for the home page
and one for the signup form. We do this in ``apps/users/urls.py``. Here's how
we define the rules:


**urls.py**

.. code-block:: python

   from tipfy import Rule

   def get_rules():
       rules = [
           Rule('/', endpoint='home', handler='apps.users.handlers.HomeHandler'),
           Rule('/accounts/signup', endpoint='auth/signup', handler='apps.users.handlers.SignupHandler'),
       ]

       return rules


These rules require two handlers that we will define now: ``HomeHandler`` and
``SignupHandler``. The first is executed when the app root is accessed, and the
later is executed when we access the ``/accounts/signup`` URL.

The home handler is only used to show if an user is autheticated or not. If not,
it will show a link for login.

The signup handler simply asks for users to choose an unique username an
provide an email address. You could extend the user model and add more fields
to the form; we are just sticking to the basics. We don't need "login" or
"logout" handlers, as this is done by App Engine.

So, here are our handlers:

**apps/users/handlers.py**

.. code-block:: python

   from google.appengine.api import users

   from tipfy import RequestHandler, request, redirect
   from tipfy.ext import auth
   from tipfy.ext.jinja2 import render_response


   class HomeHandler(RequestHandler):
       middleware = [auth.AuthMiddleware]

       def get(self, **kwargs):
           context = {
               'user':       auth.get_current_user(),
               'login_url':  auth.create_login_url(request.url),
               'logout_url': auth.create_logout_url(request.url),
           }
           return render_response('home.html', **context)


   class SignupHandler(RequestHandler):
       middleware = [auth.AuthMiddleware]

       error = None

       def get(self, **kwargs):
           context = {
               'current_url': request.url,
               'error': self.error,
           }
           return render_response('users/signup.html', **context)

       def post(self, **kwargs):
           username = request.form.get('username', '').strip()
           email = request.form.get('email', '').strip()

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
               user = auth.get_auth_system().create_user(username, auth_id,
                   **kwargs)

               if user is None:
                   # If no user is returned, the username already exists.
                   self.error = 'Username already exists. Please choose a ' \
                       'different one.'
               else:
                   # User was saved: redirect to the previous URL.
                   return redirect(request.args.get('redirect', '/'))

           return self.get()


.. note::
   The key point here is the ``AuthMiddleware`` used by the handlers. It'll
   intercept logged in users and check if they have an account created, and
   won't let them proceed before creating an account.


Both handlers use a template that we'll define now. First, the ``SignupHandler``
uses a template stored in ``templates/users/signup.html``. Here's how it looks
like:

**templates/users/signup.html**

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


And now define the template for our home in ``templates/home.html``:

**templates/home.html**

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


.. note::
   To keep things more simple and objective, we decided to not use any form
   library in this tutorial, or `Tipfy`_'s internationalization utilities.
   Form handling and i18n may be the subject for a new tutorial. :)


Time to test if it works! Open ``config.py`` and make `Tipfy`_ aware of our
users app. We do this adding our ``apps.users`` to the list of
``apps_installed`` in the configuration. `Tipfy`_ will then automatically load
the URL rules we defined previously.


Here's how our config should look like:

**config.py**

.. code-block:: python

   config = {}

   config['tipfy'] = {
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


That's it! Now our app will require users to create an account if they are
logged in, and we can handle signup requests properly.


.. _user-auth-own-tutorial:

Authentication with "own" users
-------------------------------
Authenticating with "own" users is not much different than using App Engine's
users API. We will only need to add handlers for login and logout, and we can
reuse the ``users`` app we made above with some small changes.

Let's start configuring auth system to ``tipfy.ext.auth.MultiAuth``, instead of
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
       'apps_installed': [
            'apps.users',
        ],
   }

   config['tipfy.ext.auth'] = {
       'auth_system': 'tipfy.ext.auth.MultiAuth',
   }

   config['tipfy.ext.session'] = {
       'secret_key': 'my very very very secret key',
   }


.. note::
   All modules that have configuration options list them in the session
   ``Default configuration`` in the module documentation. Take a look at the
   ones we just configured: :ref:`api.tipfy.ext.auth` and
   :ref:`api.tipfy.ext.session`.


In the ``apps/users/urls.py`` we created for the users app, add URL rules for
login and logout, in addition to the previous rules we defined:

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


The logout handler is the easiest, so let's start with it. Open
``apps/users/handlers.py`` and add our ``LogoutHandler``:

**apps/users/handlers.py**

.. code-block:: python

   from tipfy import RequestHandler, request, redirect
   from tipfy.ext import auth
   from tipfy.ext import session
   from tipfy.ext.jinja2 import render_response

   class LogoutHandler(RequestHandler):
       middleware = [session.SessionMiddleware, auth.AuthMiddleware]

       def get(self, **kwargs):
           auth.get_auth_system().logout()
           return redirect(request.args.get('redirect', '/'))


It is that simple! It just asks the auth system to logout the current user, and
then redirects to the previous URL we have set in the GET parameters, with
fallback to redirect to the home page.

.. note::
   This time we added the session middleware that will handle authentication
   sessions. This was not needed for the App Engine auth because App Engine
   itself handles the sessions.

   You could define those middleware in a base class and extend it, to avoid
   repeating the middleware definitions for each handler.


The login handler is not much harder: we just need to display a login form
and then verify an username and password when it is submitted. Add it to your
handlers file:

**apps/users/handlers.py**

.. code-block:: python

   class LoginHandler(RequestHandler):
       middleware = [session.SessionMiddleware, auth.AuthMiddleware]

       error = None

       def get(self, **kwargs):
           if auth.get_current_user() is not None:
               # Don't allow existing users to access this page.
               return redirect(request.args.get('redirect', '/'))

           context = {
               'current_url': request.url,
               'signup_url': auth.create_signup_url(request.url),
               'error': self.error,
           }

           return render_response('users/login.html', **context)

       def post(self, **kwargs):
           if auth.get_current_user() is not None:
               # Don't allow existing users to access this page.
               return redirect(request.args.get('redirect', '/'))

           # Get all posted data.
           username = request.form.get('username', '').strip()
           password = request.form.get('password', '').strip()
           remember = request.form.get('remember', '') == 'y'

           if auth.get_auth_system().login_with_form(username, password, remember):
               # Redirect to the original URL after login.
               return redirect(request.args.get('redirect', '/'))
           else:
               self.error = 'Username or password invalid. Please try again.'

           return self.get()


The function that authenticates the user is
``login_with_form(username, password, remember)``. If the username and password
are valid, the auth system will load the user and persist an user session.

If "Remember me on this computer" is checked, the user will be kept login even
if it ends the current session closing the browsing window. This is done using
secure cookies and an unique token that is renewed from time to time, following
best security practices.


The login handler uses a template that we will save in
``templates/users/login.html``. Here it is:

**templates/users/login.html**

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


One step left! Now we only need to adapt our previous signup handler to add
a password field. Let's do it:

**apps/users/handlers.py**

.. code-block:: python

   class SignupHandler(RequestHandler):
       middleware = [session.SessionMiddleware, auth.AuthMiddleware]

       error = None

       def get(self, **kwargs):
           context = {
               'current_url': request.url,
               'error': self.error,
           }
           return render_response('users/signup.html', **context)

       def post(self, **kwargs):
           username = request.form.get('username', '').strip()
           email = request.form.get('email', '').strip()
           password = request.form.get('password', '').strip()
           confirm_password = request.form.get('confirm_password', '').strip()

           if not password:
               self.error = 'Please provide a password.'
               return self.get()
           elif password != confirm_password:
               self.error = 'Passwords didn\'t match. Please try again.'
               return self.get()

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
               user = auth.get_auth_system().create_user(username, auth_id,
                   **kwargs)

               if user is None:
                   # If no user is returned, the username already exists.
                   self.error = 'Username already exists. Please choose a ' \
                       'different one.'
               else:
                   # User was saved: redirect to the previous URL.
                   return redirect(request.args.get('redirect', '/'))

           return self.get()


The key here is the function ``create_user()``, which will generate a hash for
the password and save the new user to datastore.

Also adapt the template in ``templates/users/signup.html`` to add fields for
password and password confirmation:

**templates/users/signup.html**

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
