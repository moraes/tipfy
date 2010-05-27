# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.appstats
"""
import unittest

from nose.tools import raises

import _base


from tipfy import local, NotFound, Tipfy
from tipfy.ext.appstats import AppstatsMiddleware

class TestAppstatsMiddleware(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None
        local.__release_local__()

    def test_pre_run_app_no_dev(self):
        app = Tipfy({
            'tipfy': {
                'middleware': ['tipfy.ext.appstats.AppstatsMiddleware'],
            }
        })

        middleware = AppstatsMiddleware()
        new_app = middleware.pre_run_app(app)

        self.assertEqual(new_app.__name__, 'appstats_wsgi_wrapper')

