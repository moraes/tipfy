"""
test for miscelaneous deprecated stuff.
"""
import unittest

from tipfy import Request, RequestHandler, Response, Rule, Tipfy


class TestHandler(unittest.TestCase):
    def test_dispatch(self):
        class HomeHandler(RequestHandler):
            def get(self, **kwargs):
                return Response('Home sweet home!')

        app = Tipfy(rules=[
            Rule('/', endpoint='home', handler=HomeHandler),
        ], debug=True)

        handler = HomeHandler(app, Request.from_values('/'))
        response = handler.dispatch('get')
        self.assertEqual(response.data, 'Home sweet home!')
