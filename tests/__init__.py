import unittest

import tipfy
from tipfy.app import local


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.appengine = tipfy.app.APPENGINE
        self.dev_appserver = tipfy.app.DEV_APPSERVER

    def tearDown(self):
        tipfy.app.APPENGINE = self.appengine
        tipfy.app.DEV_APPSERVER = self.dev_appserver
        local.__release_local__()

    def _set_dev_server_flag(self, flag):
        tipfy.app.APPENGINE = flag
        tipfy.app.DEV_APPSERVER = flag


class CurrentHandlerContext(object):
    def __init__(self, app, *args, **kwargs):
        self.app = app
        self.request = tipfy.Request.from_values(*args, **kwargs)

    def __enter__(self):
        match = self.app.router.match(self.request)
        self.app.router.dispatch(self.app, self.request, match)
        return local.current_handler

    def __exit__(self, type, value, traceback):
        local.__release_local__()
