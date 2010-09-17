# -*- coding: utf-8 -*-
"""
    tipfy.debugger
    ~~~~~~~~~~~~~~

    Debugger extension, to be used in development only.

    Applies monkeypatch for Werkzeug's interactive debugger to work with
    the development server. See http://dev.pocoo.org/projects/jinja/ticket/349

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import os
import sys

from tipfy.template import Loader

__version__ = '0.6'
__version_info__ = tuple(int(n) for n in __version__.split('.'))


# The template loader.
loader = Loader(os.path.abspath(os.path.join(os.path.dirname(__file__),
    'templates')))


# werkzeug.debug.utils
def get_template(filename):
    return loader.load(filename)


def render_template(filename, **context):
    return get_template(filename).generate(**context)


def get_debugged_app(app):
    if app.dev:
        apply_monkeypatches()
        from werkzeug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

    return app


def apply_monkeypatches():
    def seek(self, n, mode=0):
        pass

    def readline(self):
        if len(self._buffer) == 0:
            return ''
        ret = self._buffer[0]
        del self._buffer[0]
        return ret

    # Patch utils first, to avoid loading Werkzeug's template.
    sys.modules['werkzeug.debug.utils'] = sys.modules[__name__]

    # Apply all other patches.
    from werkzeug.debug.console import HTMLStringO
    HTMLStringO.seek = seek
    HTMLStringO.readline = readline
