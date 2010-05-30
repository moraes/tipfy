from tipfy import RequestHandler, Response
from tipfy.ext.session import SessionMiddleware
from tipfy.ext.auth import AuthMiddleware, get_current_user


class HomeHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('Hello, World!')


class HandlerWithException(RequestHandler):
    def get(self, **kwargs):
        raise ValueError('ooops!')


class SimpleAuthHandler(RequestHandler):
    middleware = [SessionMiddleware, AuthMiddleware]

    def get(self, **kwargs):
        user = get_current_user()
        if user:
            r = 'username=%s' % user.username
        else:
            r = 'no user'

        return Response(r)

