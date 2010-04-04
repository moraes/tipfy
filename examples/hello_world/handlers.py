from tipfy import render_json_response, request, RequestHandler, Response
from tipfy.ext.jinja2 import render_response

class HelloWorldHandler(RequestHandler):
    """The simplest Tipfy handler example."""
    def get(self, **kwargs):
        return Response('Hello, World!')


class HelloJinjaHandler(RequestHandler):
    """A handler that outputs the result of a rendered template."""
    def get(self, **kwargs):
        return render_response('hello.html', message='Hello, Jinja!')


class HelloJsonHandler(RequestHandler):
    """A handler that outputs a JSON string."""
    def get(self, **kwargs):
        context = {'message': 'Hello, Json!'}
        return render_json_response(context)


class HelloAjaxHandler(RequestHandler):
    """A handler that sends a different output for requests using AJAX."""
    def get(self, **kwargs):
        context = {'message': 'Hello, Ajax!'}
        if request.is_xhr:
            return render_json_response(context)
        else:
            return render_response('hello.html', **context)
