# -*- coding: utf-8 -*-
"""
    Tests for tipfy.appengine.mail
"""
import os
import sys
import unittest

from tipfy import Rule, Tipfy
from tipfy.app import local

from google.appengine.api.xmpp import Message as ApiMessage


MESSAGE = """Subject: Hello there!
From: Me <me@myself.com>
To: You <you@yourself.com>
Content-Type: text/plain; charset=ISO-8859-1

Test message!"""


def get_app():
    return Tipfy(rules=[
        Rule('/', name='xmpp-test', handler='resources.mail_handlers.MailHandler'),
        Rule('/test2', name='xmpp-test', handler='resources.mail_handlers.MailHandler2'),
    ], debug=True)


class TestInboundMailHandler(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        local.__release_local__()

    def test_mail(self):
        app = get_app()
        client = app.get_test_client()

        response = client.open(method='POST', path='/', data=MESSAGE, content_type='text/plain')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, 'Test message!')

    def test_not_implemented(self):
        app = get_app()
        app.config['tipfy']['enable_debugger'] = False
        client = app.get_test_client()

        self.assertRaises(NotImplementedError, client.open, method='POST', path='/test2', data=MESSAGE, content_type='text/plain')
