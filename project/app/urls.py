# -*- coding: utf-8 -*-
"""URL definitions."""
from tipfy.routing import Rule

rules = [
    Rule('/', name='hello-world', handler='hello_world.handlers.HelloWorldHandler'),
    Rule('/pretty', name='hello-world-pretty', handler='hello_world.handlers.PrettyHelloWorldHandler'),
]
