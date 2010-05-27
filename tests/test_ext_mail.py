# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.mail
"""
import os
import sys
import unittest

from nose.tools import raises

import _base

from tipfy import local, Map, Rule, Tipfy

from google.appengine.api.xmpp import Message as ApiMessage


MESSAGE = """Subject: Hello there!
From: Me <me@myself.com>
To: You <you@yourself.com>
Content-Type: text/plain; charset=ISO-8859-1

Test message!"""


def get_url_map():
    # Fake get_rules() for testing.
    rules = [
        Rule('/', endpoint='xmpp-test', handler='files.app.mail_handlers.MailHandler'),
        Rule('/test2', endpoint='xmpp-test', handler='files.app.mail_handlers.MailHandler2'),
    ]

    return Map(rules)


def get_app():
    return Tipfy({
        'tipfy': {
            'url_map': get_url_map(),
            'dev': True,
        },
    })


class TestInboundMailHandler(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        Tipfy.app = Tipfy.request = None
        local.__release_local__()

    def test_mail(self):
        app = get_app()
        client = app.get_test_client()

        response = client.open(method='POST', path='/', data=MESSAGE, content_type='text/plain')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Test message!')

    @raises(NotImplementedError)
    def test_not_implemented(self):
        app = get_app()
        client = app.get_test_client()

        client.open(method='POST', path='/test2', data=MESSAGE, content_type='text/plain')
