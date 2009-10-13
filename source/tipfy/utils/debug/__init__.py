# -*- coding: utf-8 -*-
"""
    tipfy.utils.debug
    ~~~~~~~~~~~~~~~~~

    Monkey patch to make Werkeug's debugger work in App Engine.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from os.path import join, dirname
from jinja2 import Environment, FileSystemLoader

import inspect
inspect.getsourcefile = inspect.getfile

env = Environment(loader=FileSystemLoader([join(dirname(__file__),
    'templates')]))

def get_template(filename):
    return env.get_template(filename)

def render_template(template_filename, **context):
    return get_template(template_filename).render(**context)
