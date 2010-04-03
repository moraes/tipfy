from tipfy import RequestHandler, request, redirect
from tipfy.ext import auth
from tipfy.ext import session
from tipfy.ext.jinja2 import render_response


class HomeHandler(RequestHandler):
    middleware = [session.SessionMiddleware, auth.AuthMiddleware]

    def get(self, **kwargs):
        context = {
            'user':       auth.get_current_user(),
            'login_url':  auth.create_login_url(request.url),
            'logout_url': auth.create_logout_url(request.url),
        }
        return render_response('home.html', **context)


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


class LogoutHandler(RequestHandler):
    middleware = [session.SessionMiddleware, auth.AuthMiddleware]

    def get(self, **kwargs):
        auth.get_auth_system().logout()
        return redirect(request.args.get('redirect', '/'))
