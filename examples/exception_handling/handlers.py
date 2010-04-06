from tipfy import RequestHandler, Response
from tipfy.ext.jinja2 import render_response

from exception_handler import ExceptionMiddleware


class HandlerExceptionMiddleware(object):
    """A middleware to handle exceptions for a particular handler or group of
    handlers.
    """
    def handle_exception(self, e, handler=None):
        response = render_response('handler_exception.html')
        response.status_code = 500
        return response


class HomeHandler(RequestHandler):
    """Just to show links to our examples."""
    def get(self):
        return render_response('home.html')


class Example1Handler(RequestHandler):
    """This handler doesn't have a middleware to handle exceptions, so all
    exceptions are handled by the application middleware.
    """
    def get(self):
        raise ValueError('Ooops.')


class Example2Handler(RequestHandler):
    """This handler uses an special middleware to handle exceptions."""
    middleware = [HandlerExceptionMiddleware]

    def get(self):
        raise ValueError('Ooops.')


class Example3Handler(RequestHandler):
    """This handler uses the same middleware used by the application to handle
    exceptions -- yes we can also do that.
    """
    middleware = [ExceptionMiddleware]

    def get(self):
        raise ValueError('Ooops.')
