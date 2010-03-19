# -*- coding: utf-8 -*-
"""
    tipfy
    ~~~~~

    Minimalist WSGI application and utilities for App Engine.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import os

# Werkzeug swiss knife.
import werkzeug
from werkzeug import cached_property, escape, import_string, Request, Response
from werkzeug.exceptions import (BadGateway, BadRequest, Forbidden, Gone,
    HTTPException, InternalServerError, LengthRequired, MethodNotAllowed,
    NotAcceptable, NotFound, NotImplemented, PreconditionFailed,
    RequestEntityTooLarge, RequestTimeout, RequestURITooLarge,
    ServiceUnavailable, Unauthorized, UnsupportedMediaType)
from werkzeug.routing import (EndpointPrefix, RequestRedirect, RuleTemplate,
    Subdomain, Submount)

# Variable store for a single request.
local = werkzeug.Local()
local_manager = werkzeug.LocalManager([local])

# Proxies to the three special variables set on each request.
local.app = local.request = local.response = None
app, request, response = local('app'), local('request'), local('response')

#: Default configuration values for this module. Keys are:
#:   - ``apps_installed``: A list of active app modules as a string. Default is
#:     an empty list
#:   - ``apps_entry_points``: URL entry points for the installed apps, in case
#:     their URLs are mounted using base paths.
#:   - ``extensions``: A list of extension modules as strings. A ``setup()``
#:     function from each module is called when the WSGI application is
#:     initialized. Extensions can then setup app hooks or perform other
#:     initializations. See `Extensions` in the documentation for a
#:     complete explanation. Default is an empty list.
#:   - ``server_name``: A server name hint, used to calculate current subdomain.
#:     If you plan to use dynamic subdomains, you must define the main domain
#:     here so that the subdomain can be extracted and applied to URL rules..
#:   - ``subdomain``: Force this subdomain to be used instead of extracting
#:     the subdomain from the current url.
#:   - ``url_map``: A ``werkzeug.routing.Map`` with the URL rules defined for
#:     the application. If not set, build one with rules defined in ``urls.py``
#:   - ``wsgi_app_id``: An identifier for this WSGIApplication instance, in
#:     case multiple instances are being used by the same app. This is used
#:     to identify instance specific data such as cached URL rules. Default is
#:     ``main``.
#:   - ``dev``: ``True`` is this is the development server, ``False`` otherwise.
#:     Default is the value of ``os.environ['SERVER_SOFTWARE']``.
#:   - ``app_id``: The application id. Default is the value of
#:     ``os.environ['APPLICATION_ID']``.
#:   - ``version_id``: The current deplyment version id. Default is the value
#:     of ``os.environ['CURRENT_VERSION_ID']``.
default_config = {
    'apps_installed': [],
    'apps_entry_points': {},
    'extensions': [],
    'server_name': None,
    'subdomain': None,
    'url_map': None,
    'wsgi_app_id': 'main',
    'dev': os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'),
    'app_id': os.environ.get('APPLICATION_ID', None),
    'version_id': os.environ.get('CURRENT_VERSION_ID', '1'),
    # Undocumented for now.
    'url_map_kwargs': {},
}

# All tipfy utilities.
from tipfy.application import (make_wsgi_app, RequestHandler, run_wsgi_app,
    WSGIApplication)
from tipfy.config import Config, get_config, REQUIRED_CONFIG
from tipfy.hooks import HookHandler, LazyCallable
from tipfy.routing import Rule, url_for
from tipfy.utils import (normalize_callable, redirect, redirect_to,
    render_json_response)