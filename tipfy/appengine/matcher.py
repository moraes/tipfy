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


class Matcher(RequestHandler):
    """A simple test to feed the matcher::

        class Index(RequestHandler):
            def get(self):
                schema = {str:['symbol'], float:['price']}
                matcher.subscribe(dict, 'symbol:GOOG AND price > 500', 'ikai:GOOG',
                    schema=schema, topic='Stock')
                matcher.match({'symbol': 'GOOG', 'price': 515.0}, topic='Stock')
                return "Hai"
    """
    def post(self, **kwargs):
        form = self.request.form
        sub_ids = form.getlist('id')
        topic = form['topic']
        results_count = form['results_count']
        doc = matcher.get_document(form)
        logging.info("sub_ids: %s, topic: %s, results_count: %r, doc: %r" %
            (sub_ids, topic, results_count, doc))
        return ''
