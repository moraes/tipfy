# -*- coding: utf-8 -*-
"""
    Tests for tipfy.application
"""
import unittest

from nose.tools import raises

import _base

import tipfy
from tipfy import local, NotFound, WSGIApplication
from tipfy.ext.appstats import AppstatsMiddleware

class TestAppstatsMiddleware(unittest.TestCase):
    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_pre_run_app_no_dev(self):
        app = WSGIApplication({
            'tipfy': {
                'middleware': ['tipfy.ext.appstats.AppstatsMiddleware'],
            }
        })

        middleware = AppstatsMiddleware()
        new_app = middleware.pre_run_app(app)

        self.assertEqual(new_app.__name__, 'appstats_wsgi_wrapper')

