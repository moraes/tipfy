import unittest

from tipfy import RequestHandler, Rule, Tipfy, redirect


class TestHandler(unittest.TestCase):
    def test_redirect(self):
        class Handler1(RequestHandler):
            def get(self, **kwargs):
                return redirect(self.request.url_for('test2'))

        class Handler2(RequestHandler):
            def get(self, **kwargs):
                return 'Hello, World!'

        rules = [
            Rule('/1', endpoint='test1', handler=Handler1),
            Rule('/2', endpoint='test2', handler=Handler2),
        ]

        app = Tipfy(rules=rules)
        client = app.get_test_client()
        response = client.get('/1', follow_redirects=True)

        assert response.data == 'Hello, World!'
