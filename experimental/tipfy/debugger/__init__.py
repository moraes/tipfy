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


def DebuggerMiddleware(app):
    apply_monkeypatches()
    from werkzeug import DebuggedApplication
    app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)
    return app


def get_template(filename):
    """Replaces ``werkzeug.debug.utils.get_template()``."""
    from tipfy.template import Loader
    loader = Loader(os.path.abspath(os.path.join(os.path.dirname(__file__),
        'templates')))
    return loader.load(filename)


def render_template(filename, **context):
    """Replaces ``werkzeug.debug.utils.render_template()``."""
    return get_template(filename).generate(**context)


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
