# -*- coding: utf-8 -*-
"""
    tipfy.appengine.matcher
    ~~~~~~~~~~~~~~~~~~~~~~~

    A RequestHandler for the `google.appengine.api.matcher`API.

    :copyright: 2010 by tipfy.org.
    :license: Apache Software License, see LICENSE.txt for more details.
"""
import logging

from google.appengine.api import matcher

from tipfy import RequestHandler


class MatcherHandler(RequestHandler):
    def get_document(self):
        return matcher.get_document(self.request.form)
