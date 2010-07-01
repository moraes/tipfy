# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.session datastore backend
"""
from datetime import datetime, timedelta
import unittest

from nose.tools import raises
from gaetestbed import DataStoreTestCase, MemcacheTestCase

from google.appengine.api import memcache
from google.appengine.ext import db

from werkzeug.contrib.securecookie import SecureCookie

from tipfy import Request, Tipfy
from tipfy.ext.session import (SessionStore, SessionMiddleware)


def get_request(app, *args, **kwargs):
    request = Request.from_values(*args, **kwargs)
    app.set_request(request)
    return request


def get_config(app):
    config = app.get_config('tipfy.ext.session').copy()
    config['cookie_args'] = {
        'session_expires': config.get('cookie_session_expires'),
        'max_age':         config.get('cookie_max_age'),
        'domain':          config.get('cookie_domain'),
        'path':            config.get('cookie_path'),
        'secure':          config.get('cookie_secure'),
        'httponly':        config.get('cookie_httponly'),
        'force':           config.get('cookie_force'),
    }
    return config


class TestSessionStore(DataStoreTestCase, MemcacheTestCase,
    unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)
        MemcacheTestCase.setUp(self)
        self.app = Tipfy({
            'tipfy.ext.session': {
                'secret_key': 'test',
            },
        })

    def test_get_flash(self):
        config = self.app.get_config('tipfy.ext.session')
        self.assertEqual(config, None)

    def whoatest_get_flash(self):
        config = get_config(self.app)

        self.assertEqual(config, None)

        assert config['cookie_name'] == 'tipfy.sesss'

        cookie = SecureCookie({'_flashes': [('foo', 'bar')]},
            secret_key=config['secret_key'])

        request = get_request(self.app, headers={
            'Cookie':   'tipfy.session=%s' % cookie.serialize(),
        })

        backends = SessionMiddleware.default_backends
        store = SessionStore(request, config, backends, 'securecookie')

        flash = store.get_flash()
        assert isinstance(flash, list)
        assert len(flash) == 1
        assert flash[0] == ('foo', 'bar')

        # The second time should not work.
        flash = store.get_flash()
        assert flash == []
