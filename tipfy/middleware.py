# -*- coding: utf-8 -*-
"""
    tipfy.middleware
    ~~~~~~~~~~~~~~~~

    Miscelaneous handler middleware classes.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from werkzeug import ETagResponseMixin


class ETagMiddleware(object):
    """Adds an etag to all responses if they haven't already set one, and
    returns '304 Not Modified' if the request contains a matching etag.
    """
    def after_dispatch(self, handler, response):
        """Called after the class:`tipfy.RequestHandler` method was executed.

        :param handler:
            A class:`tipfy.RequestHandler` instance.
        :param response:
            A class:`tipfy.Response` instance.
        :returns:
            A class:`tipfy.Response` instance.
        """
        if not isinstance(response, ETagResponseMixin):
            return response

        response.add_etag()

        if handler.request.if_none_match.contains_raw(response.get_etag()[0]):
            return handler.app.response_class(status=304)

        return response
