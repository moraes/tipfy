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
import mimetypes
import os
import sys
import zipfile

from werkzeug.wrappers import BaseResponse as Response


def debugger_wsgi_middleware(app):
    DebuggedApplication = get_debugged_application()
    return DebuggedApplication(app, evalex=True)


def get_template(filename):
    """Replaces ``werkzeug.debug.utils.get_template()``."""
    from tipfy.template import Loader, ZipLoader
    try:
        loader = Loader(os.path.join(os.path.dirname(__file__), 'templates'))
        return loader.load(filename)
    except IOError, e:
        loader = ZipLoader('lib/dist.zip', 'tipfy/debugger/templates')
        return loader.load(filename)


def render_template(filename, **context):
    """Replaces ``werkzeug.debug.utils.render_template()``."""
    return get_template(filename).generate(**context)


def get_debugged_application():
    def get_resource_with_zip(self, request, filename):
        """Return a static resource from the shared folder."""
        response = get_resource(self, request, filename)
        if response.status_code != 404:
            return response

        mimetype = mimetypes.guess_type(filename)[0] or \
            'application/octet-stream'

        try:
            filepath = os.path.join('werkzeug', 'debug', 'shared', filename)
            f = zipfile.ZipFile('lib/dist.zip', 'r')
            response = Response(f.read(filepath), mimetype=mimetype)
            f.close()
            return response
        except:
            pass

        return Response('Not Found', status=404)

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

    # Fallback to load resources from zip in case libraries are zipped.
    from werkzeug import DebuggedApplication
    get_resource = DebuggedApplication.get_resource
    DebuggedApplication.get_resource = get_resource_with_zip

    return DebuggedApplication
