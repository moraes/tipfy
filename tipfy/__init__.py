# -*- coding: utf-8 -*-
"""
    tipfy
    ~~~~~

    Minimalist WSGI application and utilities for App Engine.

    :copyright: 2011 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
__version__ = '1.0b'
__version_info__ = (1, 0)

#: Default configuration values for this module. Keys are:
#:
#: auth_store_class
#:     The default auth store class to use in :class:`tipfy.app.Request`.
#:     Default is `tipfy.appengine.auth.AuthStore`.
#:
#: i18n_store_class
#:     The default internationalization store class.
#:     Default is `tipfy.i18n.I18nStore`.
#:
#: session_store_class
#:     The default session store class to use in :class:`tipfy.app.Request`.
#:     Default is `tipfy.sessions.SessionStore`.
#:
#: server_name
#:     The server name used to calculate current subdomain. This only need
#:     to be defined to map URLs to subdomains. Default is None.
#:
#: default_subdomain
#:     The default subdomain used for rules without a subdomain defined.
#:     This only need to be defined to map URLs to subdomains. Default is ''.
#:
#: enable_debugger
#:     True to enable the interactive debugger when in debug mode, False
#:     otherwise. Default is True.
default_config = {
    'auth_store_class':    'tipfy.appengine.auth.AuthStore',
    'i18n_store_class':    'tipfy.i18n.I18nStore',
    'session_store_class': 'tipfy.sessions.SessionStore',
    'server_name':         None,
    'default_subdomain':   '',
    'enable_debugger':     True,
}

from tipfy.app import (HTTPException, Request, Response, Tipfy, abort,
    current_app, current_handler)
from tipfy.handler import RequestHandler
from tipfy.appengine import (APPENGINE, APPLICATION_ID, CURRENT_VERSION_ID,
    DEV_APPSERVER)
from tipfy.config import DEFAULT_VALUE, REQUIRED_VALUE
from tipfy.routing import HandlerPrefix, NamePrefix, Rule, Subdomain, Submount
