# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.appstats
"""
import unittest

from nose.tools import raises

from tipfy import Tipfy
from tipfy.ext.appstats import AppstatsMiddleware


class TestAppstatsMiddleware(unittest.TestCase):
    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_post_make_app_no_dev(self):
        app = Tipfy({
            'tipfy': {
                'middleware': ['tipfy.ext.appstats.AppstatsMiddleware'],
            }
        })

        middleware = AppstatsMiddleware()
        new_app = middleware.post_make_app(app)

        self.assertEqual(new_app.wsgi_app.__name__, 'appstats_wsgi_wrapper')




