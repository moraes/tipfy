# -*- coding: utf-8 -*-
"""
    urls
    ~~~~

    URL definitions.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import app, import_string

urls = []

for app_module in app.config.apps_installed:
    try:
        # Load the urls module from the app and extend our rules.
        app_urls = import_string('%s.urls:urls' % app_module)
        urls.extend(app_urls)
    except ImportError:
        pass
