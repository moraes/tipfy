# -*- coding: utf-8 -*-
"""
    tipfy.testing
    ~~~~~~~~~~~~~

    Unit test utilities.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from .app import local


class CurrentHandlerContext(object):
    """Returns a handler set as a current handler. The handler instance
    or class can be passed explicitly or request values can be passed to
    match a handler in the app router.

    This is intended to be used with a `with` statement::

        from __future__ import with_statement

        from tipfy import Tipfy, Rule

        app = Tipfy(rules=[
            Rule('/about', name='home', handler='handlers.AboutHandler'),
        ])

        with app.get_test_handler('/about') as handler:
            self.assertEqual(handler.url_for('/', _full=True),
                'http://localhost/about')

    The context will set the request and current_handler and clean it up
    after the execution.
    """
    def __init__(self, app, *args, **kwargs):
        """Initializes the handler context.

        :param app:
            A :class:`tipfy.Tipfy` instance.
        :param args:
            Arguments to build a :class:`tipfy.Request` instance if a request
            is not passed explicitly.
        :param kwargs:
            Keyword arguments to build a :class:`Request` instance if a request
            is not passed explicitly. A few keys have special meaning:

            - `request`: a :class:`Request` object. If not passed, a new
              request is built using the passed `args` and `kwargs`. If
              `handler` or `handler_class` are not passed, the request is used
              to match a handler in the app router.
            - `handler_class`: instantiate this handler class instead of
              matching one using the request object.
            - `handler`: a handler instance. If passed, the handler is simply
              set and reset as current_handler during the context execution.
        """
        self.app = app
        self.handler = kwargs.pop('handler', None)
        self.handler_class = kwargs.pop('handler_class', None)
        self.request = kwargs.pop('request', None)
        if self.request is None:
            self.request = app.request_class.from_values(*args, **kwargs)

    def __enter__(self):
        if self.handler is not None:
            local.current_handler = self.handler
        else:
            if self.handler_class is None:
                match = self.app.router.match(self.request)
                spec = self.app.router.get_dispatch_spec(self.request, match)
                handler_class, method, kwargs = spec
            else:
                handler_class = self.handler_class

            local.current_handler = handler_class(self.app, self.request)

        return local.current_handler

    def __exit__(self, type, value, traceback):
        local.__release_local__()
