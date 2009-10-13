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

# Directory for compiled templates. If None, don't use compiled templates.
templates_compiled_dir = 'templates_compiled'

# Default locale.
locale = 'en_US'

# Timezone difference from UTC: a datetime.timedelta object or 0.
time_diff = 0

# Secret phrase for session's secure cookies.
session_secret_key = None
