# -*- coding: utf-8 -*-
"""URL definitions."""
from tipfy import Rule

def get_rules(app):
    """Returns a list of URL rules for the Hello, World! application.

    :param app:
        The WSGI application instance.
    :return:
        A list of class:`tipfy.Rule` instances.
    """
    rules = [
        Rule('/', endpoint='hello-world', handler='hello_world.handlers.HelloWorldHandler'),
        Rule('/pretty', endpoint='hello-world-pretty', handler='hello_world.handlers.PrettyHelloWorldHandler'),
    ]

    return rules
