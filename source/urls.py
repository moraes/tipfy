# -*- coding: utf-8 -*-
"""
    urls
    ~~~~

    URL definitions.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import get_config, import_string, Rule

def get_rules():
    rules = []

    for app_module in get_config('tipfy', 'apps_installed'):
        try:
            # Load the urls module from the app and extend our rules.
            app_urls = import_string('%s.urls' % app_module)
            rules.extend(app_urls.get_rules())
        except ImportError:
            pass

    return rules
