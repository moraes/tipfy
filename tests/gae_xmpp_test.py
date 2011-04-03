# -*- coding: utf-8 -*-
"""
    Tests for tipfy.appengine.xmpp
"""
import os
import sys
import unittest

from tipfy import Rule, Tipfy
from tipfy.app import local

from google.appengine.api.xmpp import Message as ApiMessage

import test_utils

fake_local = {}


def get_app():
    return Tipfy(rules=[
        Rule('/', name='xmpp-test', handler='resources.xmpp_handlers.XmppHandler'),
        Rule('/test2', name='xmpp-test', handler='resources.xmpp_handlers.XmppHandler2'),
    ], debug=True)


def send_message(jids, body, from_jid=None, message_type='chat',
                 raw_xml=False):
    fake_local['message'] = {
        'body': body,
    }


class InvalidMessageError(Exception):
    pass


class Message(ApiMessage):
    """Encapsulates an XMPP message received by the application."""
    def __init__(self, vars):
        """Constructs a new XMPP Message from an HTTP request.

        Args:
          vars: A dict-like object to extract message arguments from.
        """
        try:
            self.__sender = vars["from"]
            self.__to = vars["to"]
            self.__body = vars["body"]
        except KeyError, e:
            raise InvalidMessageError(e[0])

        self.__command = None
        self.__arg = None

    def reply(self, body, message_type='chat', raw_xml=False,
            send_message=send_message):
        """Convenience function to reply to a message.

        Args:
          body: str: The body of the message
          message_type, raw_xml: As per send_message.
          send_message: Used for testing.

        Returns:
          A status code as per send_message.

        Raises:
          See send_message.
        """
        return send_message([self.sender], body, from_jid=self.to,
                        message_type=message_type, raw_xml=raw_xml)


class TestCommandHandler(test_utils.BaseTestCase):
    def setUp(self):
        from tipfy.appengine import xmpp
        self.xmpp_module = xmpp.xmpp
        xmpp.xmpp = sys.modules[__name__]
        test_utils.BaseTestCase.setUp(self)

    def tearDown(self):
        fake_local.clear()

        from tipfy.appengine import xmpp
        xmpp.xmpp = self.xmpp_module
        test_utils.BaseTestCase.tearDown(self)

    def test_no_command(self):
        app = get_app()
        client = app.get_test_client()

        data = {}
        client.open(method='POST', data=data)

        self.assertEqual(fake_local.get('message', None), None)

    def test_not_implemented(self):
        app = get_app()
        app.config['tipfy']['enable_debugger'] = False
        client = app.get_test_client()

        data = {
            'from': 'me@myself.com',
            'to':   'you@yourself.com',
            'body': '/inexistent_command foo bar',
        }
        self.assertRaises(NotImplementedError, client.post, path='/test2', data=data)

    def test_unknown_command(self):
        app = get_app()
        client = app.get_test_client()

        data = {
            'from': 'me@myself.com',
            'to':   'you@yourself.com',
            'body': '/inexistent_command foo bar',
        }
        client.open(method='POST', data=data)

        self.assertEqual(fake_local.get('message', None), {'body': 'Unknown command'})

    def test_command(self):
        app = get_app()
        client = app.get_test_client()

        data = {
            'from': 'me@myself.com',
            'to':   'you@yourself.com',
            'body': '/foo foo bar',
        }
        client.open(method='POST', data=data)

        self.assertEqual(fake_local.get('message', None), {'body': 'Foo command!'})

        data = {
            'from': 'me@myself.com',
            'to':   'you@yourself.com',
            'body': '/bar foo bar',
        }
        client.open(method='POST', data=data)

        self.assertEqual(fake_local.get('message', None), {'body': 'Bar command!'})

    def test_text_message(self):
        app = get_app()
        client = app.get_test_client()

        data = {
            'from': 'me@myself.com',
            'to':   'you@yourself.com',
            'body': 'Hello, text message!',
        }
        client.open(method='POST', data=data)

        self.assertEqual(fake_local.get('message', None), {'body': 'Hello, text message!'})


if __name__ == '__main__':
    test_utils.main()
