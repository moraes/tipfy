# -*- coding: utf-8 -*-
"""
    tipfy.ext.session
    ~~~~~~~~~~~~~~~~~

    Session extension.

    This module provides sessions using secure cookies or the datastore.

    .. note::
       The session implementations are still pretty new and untested.
       Consider this as a work in progress.

    This module derives from `Kay`_.

    :copyright: (c) 2009 Accense Technology, Inc. All rights reserved.
    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import local

#: Default configuration values for this module. Keys are:
#: A dictionary of configuration options for ``tipfy.ext.session``. Keys are:
#:   - ``secret_key``: Secret key to generate session cookies. Set this to
#:     something random and unguessable. Default is
#:     `please-change-me-it-is-important`.
#:   - ``expiration``: Session expiration time in seconds. Default is `86400`.
#:   - ``cookie_name``: Name of the cookie to save the session. Default is
#:     `tipfy.session`.
#:   - ``id_cookie_name``:Name of the cookie to save the session id. Default is
#:     `tipfy.session_id`.
default_config = {
    'secret_key': 'please-change-me-it-is-important',
    'expiration': 86400,
    'cookie_name': 'tipfy.session',
    'id_cookie_name': 'tipfy.session_id',
}

# Proxies to the session variables set on each request.
local.session = local.session_store = None
session, session_store = local('session'), local('session_store')
