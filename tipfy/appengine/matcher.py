# -*- coding: utf-8 -*-
"""
    tipfy.appengine.matcher
    ~~~~~~~~~~~~~~~~~~~~~~~

    A RequestHandler for the `google.appengine.api.matcher`API.

    :copyright: 2010 by tipfy.org.
    :license: Apache Software License, see LICENSE.txt for more details.
"""
from google.appengine.api import matcher

from tipfy import RequestHandler


class MatcherHandler(RequestHandler):
    """A simple test to feed the matcher::

        class Index(RequestHandler):
            def get(self):
                schema = {str:['symbol'], float:['price']}
                matcher.subscribe(dict, 'symbol:GOOG AND price > 500', 'ikai:GOOG',
                    schema=schema, topic='Stock')
                matcher.match({'symbol': 'GOOG', 'price': 515.0}, topic='Stock')
                return "Queued"

    """
    def post(self, **kwargs):
        """Parses all the fields out of a match and pass along."""
        form = self.request.form
        result = self.match(
            sub_ids=form.getlist('id'),
            key=form.get('key'),
            topic=form['topic'],
            results_count=int(form['results_count']),
            results_offset=int(form['results_offset']),
            doc=matcher.get_document(form),
            **kwargs
        )
        return result

    def match(self, sub_ids, topic, results_count, results_offset, key, doc):
        """Receives a match document.

        Override this method to implement a match handler.

        :param sub_ids:
            A list of subscription ID's (strings) which matched the document.
        :param topic:
            The topic or model name, e.g. "StockOptions"
        :param results_count:
            The total number of subscription ids matched across all batches.
        :param results_offset:
            The offset of the current batch into the results_count.
        :param key:
            The result_key provided by the user in the Match call.
        :param doc:
            The matched document itself. May be an Entity, db.Model
            instance, or dict.
        """
        raise NotImplementedError()
