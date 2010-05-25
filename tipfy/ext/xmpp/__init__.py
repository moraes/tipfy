# -*- coding: utf-8 -*-
"""
    tipfy.ext.xmpp
    ~~~~~~~~~~~~~~

    XMPP webapp handler classes.

    This module provides handler classes for XMPP bots, including both basic
    messaging functionality and a command handler for commands such as
    "/foo bar".

    Ported from the original App Engine library.

    :copyright: 2007 Google Inc.
    :license: Apache 2.0 License, see LICENSE.txt for more details.
"""
import logging

from google.appengine.api import xmpp

from tipfy import RequestHandler


class BaseHandler(RequestHandler):
    """A webapp baseclass for XMPP handlers.

    Implements a straightforward message delivery pattern. When a message is
    received, message_received is called with a Message object that
    encapsulates the relevant details. Users can reply using the standard XMPP
    API, or the convenient .reply() method on the Message object.
    """
    def message_received(self, message):
        """Called when a message is sent to the XMPP bot.

        :param message:
            The message that was sent by the user.
        """
        raise NotImplementedError()

    def post(self, **kwargs):
        try:
            self.xmpp_message = xmpp.Message(self.request.form)
        except xmpp.InvalidMessageError, e:
            logging.error('Invalid XMPP request: Missing required field %s',
                e[0])
            return ''

        return self.message_received(self.xmpp_message)


class CommandHandlerMixin(object):
    """A command handler for XMPP bots.

    Implements a command handler pattern. XMPP messages are processed by
    calling message_received. Message objects handled by this class are
    annotated with 'command' and 'arg' fields. On receipt of a message
    starting with a forward or backward slash, the handler calls a method
    named after the command - eg, if the user sends "/foo bar", the handler
    will call foo_command(message). If no handler method matches,
    unhandled_command is called. The default behaviour of unhandled_command
    is to send the message "Unknown command" back to the sender.

    If the user sends a message not prefixed with a slash,
    text_message(message) is called.
    """
    def unhandled_command(self, message):
        """Called when an unknown command is sent to the XMPP bot.

        :param message:
            Message: The message that was sent by the user.
        """
        message.reply('Unknown command')

    def text_message(self, message):
        """Called when a message not prefixed by a /command is sent to the XMPP
        bot.

        :param message:
            Message: The message that was sent by the user.
        """
        pass

    def message_received(self, message):
        """Called when a message is sent to the XMPP bot.

        :param message:
            Message: The message that was sent by the user.
        """
        if message.command:
            handler_name = '%s_command' % (message.command,)
            handler = getattr(self, handler_name, None)
            if handler:
                handler(message)
            else:
                self.unhandled_command(message)
        else:
            self.text_message(message)

        return ''


class CommandHandler(CommandHandlerMixin, BaseHandler):
    """A implementation of CommandHandlerMixin."""
    pass
