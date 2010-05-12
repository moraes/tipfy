import tipfy
from tipfy.ext.session import SessionMiddleware
from tipfy.ext.auth import AuthMiddleware, get_current_user


class HomeHandler(tipfy.RequestHandler):
    def get(self, **kwargs):
        return tipfy.Response('Hello, World!')


class HandlerWithException(tipfy.RequestHandler):
    def get(self, **kwargs):
        raise ValueError('ooops!')


class AuthHandler(tipfy.RequestHandler):
    middleware = [SessionMiddleware, AuthMiddleware]

    def get(self, **kwargs):
        user = get_current_user()
        if user:
            r = 'username=%s' % user.username
        else:
            r = 'no user'

        return tipfy.Response(r)
