# -*- coding: utf-8 -*-
"""
    urls
    ~~~~

    URL definitions.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import tipfy

def get_rules():
    """Returns a list of URL rules for the application. The list can be defined
    entirely here or in separate ``urls.py`` files. Here we show an example of
    joining all rules from the ``apps_installed`` listed in config.
    """
    rules = []

    for app_module in tipfy.get_config('tipfy', 'apps_installed'):
        try:
            # Load the urls module from the app and extend our rules.
            app_rules = tipfy.import_string('%s.urls' % app_module)
            rules.extend(app_rules.get_rules())
        except ImportError:
            pass

    return rules
