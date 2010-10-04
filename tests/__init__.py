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
