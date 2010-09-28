# -*- coding: utf-8 -*-
"""
    tipfy.debugger
    ~~~~~~~~~~~~~~

    Debugger extension, to be used in development only.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
def debugger_wsgi_middleware(app):
    from tipfy.debugger.app import DebuggedApplication
    return DebuggedApplication(app, evalex=True)
