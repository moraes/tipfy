# -*- coding: utf-8 -*-
"""
    config
    ~~~~~~

    Configuration settings.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""
from os import environ

# Are we using the development server?
dev = environ.get('SERVER_SOFTWARE', '').startswith('Dev')

# Deployment version ID.
version_id = environ.get('CURRENT_VERSION_ID', '1')

# Application ID.
app_id = environ.get('APPLICATION_ID', None)

# List of active apps.
apps_installed = []

# URL entry points for the installed apps.
apps_entry_points = {}

# Directory for templates.
templates_dir = 'templates'

# Directory for compiled templates. If None, don't use compiled templates.
templates_compiled_dir = None

# Default locale code.
locale = 'en_US'

# Timezone name according to the Olson database.
timezone = 'America/Chicago'

# Secret phrase for session's secure cookies.
session_secret_key = None

# Application middlewares.
middleware_classes = []

if dev:
    # Set the debugger middleware only when using the development server.
    middleware_classes.append('tipfy.ext.debugger:DebuggedApp')
