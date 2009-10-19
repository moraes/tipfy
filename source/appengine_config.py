# -*- coding: utf-8 -*-
"""
    appengine_config
    ~~~~~~~~~~~~~~~~

    Stores values to override default behaviors in tipfy and extensions.
    This file is not required and is kept here as a reference.

    For example, to add middlewares:

        from somewhere import MyMiddleWareClass

        def tipfy_add_middleware(app):
            app = MyMiddleWareClass(app)
            return app

    Or to use an extended Request object:

        from somewhere import MyRequestClass

        def tipfy_get_request(app, environ):
            return MyRequestClass(environ)

    Or to use an different strategy to load url rules:

        from werkzeug.routing import Map
        from my_app import my_app_rules

        def tipfy_get_url_map(app):
            return Map(my_app_rules)

    See in tipfy.config_handle the dict of overridable settings.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""
