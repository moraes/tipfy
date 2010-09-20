import os
import sys
import unittest

class TestGae(unittest.TestCase):
    def setUp(self):
        self.app_id = os.environ.get('APPLICATION_ID', None)
        self.server = os.environ.get('SERVER_SOFTWARE', None)

        os.environ['APPLICATION_ID'] = ''
        os.environ['SERVER_SOFTWARE'] = ''

        import tipfy
        reload(tipfy)

    def tearDown(self):
        import tipfy
        try:
            tipfy.Tipfy.app.clear_locals()
        except:
            pass

        if self.app_id is not None:
            os.environ['APPLICATION_ID'] = self.app_id

        if self.server is not None:
            os.environ['SERVER_SOFTWARE'] = self.server

    def test_appengine_flag(self):
        import tipfy
        self.assertEqual(tipfy.APPENGINE, False)

        os.environ['APPLICATION_ID'] = 'my-app'
        os.environ['SERVER_SOFTWARE'] = 'Development'

        reload(tipfy)
        self.assertEqual(tipfy.APPENGINE, True)

    def test_appengine_flag2(self):
        import tipfy
        self.assertEqual(tipfy.APPENGINE, False)

        os.environ['APPLICATION_ID'] = 'my-app'
        os.environ['SERVER_SOFTWARE'] = 'Google App Engine'

        reload(tipfy)
        self.assertEqual(tipfy.APPENGINE, True)

    def test_dev_run(self):
        import tipfy

        os.environ['APPLICATION_ID'] = 'my-app'
        os.environ['SERVER_SOFTWARE'] = 'Development'
        os.environ['SERVER_NAME'] = 'localhost'
        os.environ['SERVER_PORT'] = '8080'
        os.environ['REQUEST_METHOD'] = 'GET'
        reload(tipfy)

        self.assertEqual(tipfy.Tipfy.dev, True)

        res = 'Hello, World!'

        class HomeHandler(tipfy.RequestHandler):
            def get(self, **kwargs):
                return tipfy.Response(res)

        app = tipfy.Tipfy(rules=[
            tipfy.Rule('/', endpoint='home', handler=HomeHandler),
        ], debug=True)

        app.run()
        self.assertEqual(sys.stdout.getvalue(), 'Status: 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: 13\r\n\r\nHello, World!')
