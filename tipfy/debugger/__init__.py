# -*- coding: utf-8 -*-
"""
    tipfy.debugger
    ~~~~~~~~~~~~~~

    Patched DebuggedApplication to work on App Engine and using zipimport.

    Applies monkeypatch for Werkzeug's interactive debugger to work with
    the development server. See http://dev.pocoo.org/projects/jinja/ticket/349

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import mimetypes
import os
import sys
import zipfile

from tipfy.template import Loader, ZipLoader

_LOADER = None
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates')
ZIP_PATH = os.path.join('lib', 'dist.zip')


def get_loader():
    global _LOADER
    if _LOADER is None:
        if os.path.exists(TEMPLATE_PATH):
            _LOADER = Loader(TEMPLATE_PATH)
        elif os.path.exists(ZIP_PATH):
            _LOADER = ZipLoader(ZIP_PATH, 'tipfy/debugger/templates')
        else:
            raise RuntimeError('Could not find debugger templates in %r or '
                '%r.' % (TEMPLATE_PATH, ZIP_PATH))

    return _LOADER


def get_template(filename):
    """Replaces ``werkzeug.debug.utils.get_template()``."""
    return get_loader().load(filename)


def render_template(filename, **context):
    """Replaces ``werkzeug.debug.utils.render_template()``."""
    return get_template(filename).generate(**context)


# Patch utils first, to avoid loading Werkzeug's template.
sys.modules['werkzeug.debug.utils'] = sys.modules[__name__]
from werkzeug.wrappers import BaseResponse as Response
from werkzeug.debug.console import HTMLStringO
from werkzeug import DebuggedApplication as DebuggedApplicationBase


class DebuggedApplication(DebuggedApplicationBase):
    def get_resource(self, request, filename):
        """Return a static resource from the shared folder."""
        response = super(DebuggedApplication, self).get_resource(request,
            filename)
        if response.status_code != 404 or not os.path.exists(ZIP_PATH):
            return response

        filepath = os.path.join('werkzeug', 'debug', 'shared', filename)
        mimetype = mimetypes.guess_type(filename)[0] or \
            'application/octet-stream'

        f = zipfile.ZipFile(ZIP_PATH, 'r')
        try:
            response = Response(f.read(filepath), mimetype=mimetype)
            return response
        except Exception:
            pass
        finally:
            f.close()

        return Response('Not Found', status=404)


def seek(self, n, mode=0):
    pass


def readline(self):
    if len(self._buffer) == 0:
        return ''
    ret = self._buffer[0]
    del self._buffer[0]
    return ret


# Apply all other patches.
HTMLStringO.seek = seek
HTMLStringO.readline = readline
