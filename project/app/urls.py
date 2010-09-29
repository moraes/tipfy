# -*- coding: utf-8 -*-
"""URL definitions."""
from tipfy import Rule

rules = [
    Rule('/', endpoint='hello-world', handler='hello_world.handlers.HelloWorldHandler'),
    Rule('/pretty', endpoint='hello-world-pretty', handler='hello_world.handlers.PrettyHelloWorldHandler'),
]
