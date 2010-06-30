# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.session middleware
"""
import unittest
from nose.tools import raises
from gaetestbed import DataStoreTestCase, MemcacheTestCase

from google.appengine.api import memcache
from google.appengine.ext import db

from tipfy import Request, Tipfy, get_config
from tipfy.ext.session import SessionMiddleware


class TestSessionMiddleware(unittest.TestCase):
    def setUp(self):
        self.app = Tipfy

    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_config(self):
        middleware = SessionMiddleware()

        config = get_config('tipfy.ext.session').copy()
        config['cookie_args'] = {
            'session_expires': config.pop('cookie_session_expires'),
            'max_age':         config.pop('cookie_max_age'),
            'domain':          config.pop('cookie_domain'),
            'path':            config.pop('cookie_path'),
            'secure':          config.pop('cookie_secure'),
            'httponly':        config.pop('cookie_httponly'),
            'force':           config.pop('cookie_force'),
        }

        assert middleware.config == config
