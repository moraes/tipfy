# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.xmpp
"""
import os
import sys
import unittest

from nose.tools import raises

import _base

from tipfy import local, Map, Rule, Tipfy

fake_local = {}

def get_url_map():
    # Fake get_rules() for testing.
    rules = [
        Rule('/', endpoint='xmpp-test', handler='files.app.xmpp_handlers.XmppHandler'),
    ]

    return Map(rules)


def get_app():
    return Tipfy({
        'tipfy': {
            'url_map': get_url_map(),
            'dev': True,
        },
    })


class InvalidMessageError(Exception):
    pass


def send_message(jids, body, from_jid=None, message_type='chat',
                 raw_xml=False):
    fake_local['message'] = {
        'body': body,
    }


class Message(object):
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

    #import sys
    #sys.exit(self.command + ' ---> ' + self.arg)

  @property
  def sender(self):
    return self.__sender

  @property
  def to(self):
    return self.__to

  @property
  def body(self):
    return self.__body

  def __parse_command(self):
    if self.__arg != None:
      return

    body = self.__body
    if body.startswith('\\'):
      body = '/' + body[1:]

    self.__arg = ''
    if body.startswith('/'):
      parts = body.split(' ', 1)
      self.__command = parts[0][1:]
      if len(parts) > 1:
        self.__arg = parts[1].strip()
    else:
      self.__arg = self.__body.strip()

  @property
  def command(self):
    self.__parse_command()
    return self.__command

  @property
  def arg(self):
    self.__parse_command()
    return self.__arg

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


class TestCommandHandler(unittest.TestCase):
    def setUp(self):
        import tipfy.ext.xmpp
        self.xmpp_module = tipfy.ext.xmpp.xmpp
        tipfy.ext.xmpp.xmpp = sys.modules[__name__]

    def tearDown(self):
        local.__release_local__()
        fake_local.clear()

        import tipfy.ext.xmpp
        tipfy.ext.xmpp.xmpp = self.xmpp_module

    def test_no_command(self):
        app = get_app()
        client = app.get_test_client()

        data = {}
        client.open(method='POST', data=data)

        assert fake_local.get('message', None) is None

    def test_unknown_command(self):
        app = get_app()
        client = app.get_test_client()

        data = {
            'from': 'me@myself.com',
            'to':   'you@yourself.com',
            'body': '/inexistent_command foo bar',
        }
        client.open(method='POST', data=data)

        assert fake_local.get('message', None) == {'body': 'Unknown command'}

    def test_command(self):
        app = get_app()
        client = app.get_test_client()

        data = {
            'from': 'me@myself.com',
            'to':   'you@yourself.com',
            'body': '/foo foo bar',
        }
        client.open(method='POST', data=data)

        assert fake_local.get('message', None) == {'body': 'Foo command!'}

        data = {
            'from': 'me@myself.com',
            'to':   'you@yourself.com',
            'body': '/bar foo bar',
        }
        client.open(method='POST', data=data)

        assert fake_local.get('message', None) == {'body': 'Bar command!'}


