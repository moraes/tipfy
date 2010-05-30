from tipfy import RequestHandler, Response
from tipfy.ext import auth


class AuthHandler(RequestHandler):
    middleware = [auth.AuthMiddleware]

    def get(self, **kwargs):
        return Response('Hello, World!')


class SignupHandler(RequestHandler):
    middleware = [auth.AuthMiddleware]

    def get(self, **kwargs):
        return Response('Please signup!')
