import tipfy
from tipfy.ext import auth


class HomeHandler(tipfy.RequestHandler):
    def get(self, **kwargs):
        return tipfy.Response('Hello, World!')


class HandlerWithException(tipfy.RequestHandler):
    def get(self, **kwargs):
        raise ValueError('ooops!')


class AuthHandler(tipfy.RequestHandler):
    middleware = [auth.AuthMiddleware]

    def get(self, **kwargs):
        return tipfy.Response('Hello, World!')


class SignupHandler(tipfy.RequestHandler):
    middleware = [auth.AuthMiddleware]

    def get(self, **kwargs):
        return tipfy.Response('Please signup!')
