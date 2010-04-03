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
