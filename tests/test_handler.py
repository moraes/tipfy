import unittest

from tipfy import RequestHandler, Response, Rule, Tipfy


class TestHandler(unittest.TestCase):
    def test_redirect(self):
        class Handler1(RequestHandler):
            def get(self, **kwargs):
                return self.redirect(self.url_for('test2'))

        class Handler2(RequestHandler):
            def get(self, **kwargs):
                return Response('Hello, World!')

        rules = [
            Rule('/1', endpoint='test1', handler=Handler1),
            Rule('/2', endpoint='test2', handler=Handler2),
        ]

        app = Tipfy(rules=rules)
        client = app.get_test_client()
        response = client.get('/1', follow_redirects=True)

        assert response.data == 'Hello, World!'

    def test_redirect_to(self):
        class Handler1(RequestHandler):
            def get(self, **kwargs):
                return self.redirect_to('test2')

        class Handler2(RequestHandler):
            def get(self, **kwargs):
                return Response('Hello, World!')

        rules = [
            Rule('/1', endpoint='test1', handler=Handler1),
            Rule('/2', endpoint='test2', handler=Handler2),
        ]

        app = Tipfy(rules=rules)
        client = app.get_test_client()
        response = client.get('/1', follow_redirects=True)

        assert response.data == 'Hello, World!'
