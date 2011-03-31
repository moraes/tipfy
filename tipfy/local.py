# -*- coding: utf-8 -*-
"""
    tipfy.local
    ~~~~~~~~~~~

    Context-local utilities.

    :copyright: 2011 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import werkzeug.local

#: Context-local.
local = werkzeug.local.Local()


def get_app():
    """Returns the current WSGI app instance.

    :returns:
        The current :class:`tipfy.app.App` instance.
    """
    return local.app


def get_request():
    """Returns the current request instance.

    :returns:
        The current :class:`tipfy.app.Request` instance.
    """
    return local.request


#: A proxy to the active handler for a request. This is intended to be used by
#: functions called out of a handler context. Usage is generally discouraged:
#: it is preferable to pass the handler as argument when possible and only use
#: this as last alternative -- when a proxy is really needed.
#:
#: For example, the :func:`tipfy.utils.url_for` function requires the current
#: request to generate a URL. As its purpose is to be assigned to a template
#: context or other objects shared between requests, we use `current_handler`
#: there to dynamically get the currently active handler.
current_handler = local('current_handler')
#: Same as current_handler, only for the active WSGI app.
current_app = local('app')
