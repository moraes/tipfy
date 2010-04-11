.. _api.tipfy.ext.xmpp:

tipfy.ext.xmpp
==============

This module provides handler classes for XMPP bots, including both basic 
messaging functionality and a command handler for commands such as "/foo bar".

.. module:: tipfy.ext.xmpp

Handler classes
---------------
.. autoclass:: BaseHandler
   :members: message_received, handle_exception
.. autoclass:: CommandHandlerMixin
   :members: message_received, text_message, unhandled_command
