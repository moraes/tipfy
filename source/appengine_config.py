# -*- coding: utf-8 -*-
"""
    appengine_config
    ~~~~~~~~~~~~~~~~

    Stores configuration values that can override default behaviors in tipfy
    and extensions.

    This implements google.appengine.api.lib_config interface: lib_config will
    look for config replacements in this module. This file is only needed
    if a replacement is required, so it is just kept here as a reference.

    For example, to add middlewares:

        from somewhere import MyMiddleWareClass

        def tipfy_add_middleware(app):
            app = MyMiddleWareClass(app)
            return app

    Or to use an extended Request object:

        from somewhere import MyRequestClass

        def tipfy_get_request(app, environ):
            return MyRequestClass(environ)

    Or to load url rules using a different strategy:

        from werkzeug.routing import Map
        from somewhere import my_app_rules

        def tipfy_get_url_map(app):
            return Map(my_app_rules)

    See in tipfy.config_handle the full dictionary of overridable settings.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""
