# -*- coding: utf-8 -*-
"""
    tipfy.ext.debugger.patch
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Monkeypatch for Werkzeug's interactive debugger to work with the
    development server.

    See http://dev.pocoo.org/projects/jinja/ticket/349

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import sys
from os.path import join, dirname
from jinja2 import Environment, FileSystemLoader


env = Environment(loader=FileSystemLoader([join(dirname(__file__),
    'templates')]))


# werkzeug.debug.utils
def get_template(filename):
    return env.get_template(filename)


def render_template(template_filename, **context):
    return get_template(template_filename).render(**context)


# Patch utils to use Jinja templates instead.
sys.modules['werkzeug.debug.utils'] = sys.modules[__name__]
