import os
import sys
import unittest

from tipfy import Request, RequestHandler, Response, Rule, Tipfy
from tipfy.utils import json_decode, json_encode

class TestRequest(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_request_json(self):
        class HomeHandler(RequestHandler):
            def get(self, **kwargs):
                return Response(self.request.json['foo'])

        app = Tipfy(rules=[
            Rule('/', endpoint='home', handler=HomeHandler),
        ], debug=True)

        data = json_encode({'foo': 'bar'})
        client = app.get_test_client()
        response = client.get('/', content_type='application/json', data=data)
        self.assertEqual(response.data, 'bar')
