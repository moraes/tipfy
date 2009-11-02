# -*- coding: utf-8 -*-
"""
    tipfy.ext.debugger.patch
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Monkey patches for Werkzeug's interactive debugger to work with the
    development server.

    See http://dev.pocoo.org/projects/jinja/ticket/349

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import sys
import inspect
from os.path import join, dirname
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader([join(dirname(__file__),
    'templates')]))


# werkzeug.debug.utils
def get_template(filename):
    return env.get_template(filename)


def render_template(template_filename, **context):
    return get_template(template_filename).render(**context)


# werkzeug.debug.console.HTMLStringO
def flush(self):
    pass


def seek(self, n, mode=0):
    pass


def readline(self):
    if len(self._buffer) == 0:
        return ''
    ret = self._buffer[0]
    del self._buffer[0]
    return ret


# werkzeug.debug.console.ThreadedStream
def push():
    from werkzeug.debug.console import _local
    if not isinstance(sys.stdout, ThreadedStream):
        sys.stdout = ThreadedStream()
    _local.stream = HTMLStringO()


# Patch utils first, to avoid loading Werkzeug's template.
sys.modules['werkzeug.debug.utils'] = sys.modules[__name__]

# Patch inspect. getsourcefile() is empty on App Engine.
inspect.getsourcefile = inspect.getfile

# Apply all other patches.
from werkzeug.debug.console import HTMLStringO, ThreadedStream
HTMLStringO.flush = flush
HTMLStringO.seek = seek
HTMLStringO.readline = readline
ThreadedStream.push = staticmethod(push)
