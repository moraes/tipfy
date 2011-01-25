# -*- coding: utf-8 -*-
"""
    hello_world.handlers
    ~~~~~~~~~~~~~~~~~~~~

    Hello, World!: the simplest tipfy app.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""
from tipfy import RequestHandler, Response
from tipfyext.jinja2 import Jinja2Mixin

class HelloWorldHandler(RequestHandler):
    def get(self):
        """Simply returns a Response object with an enigmatic salutation."""
        return Response('Hello, World!')


class PrettyHelloWorldHandler(RequestHandler, Jinja2Mixin):
    def get(self):
        """Simply returns a rendered template with an enigmatic salutation."""
        context = {
            'message': 'Hello, World!',
        }
        return self.render_response('hello_world.html', **context)
