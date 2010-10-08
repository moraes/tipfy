# -*- coding: utf-8 -*-
"""
    tipfy.appengine.mail
    ~~~~~~~~~~~~~~~~~~~~

    A simple RequestHandler to help with receiving mail.

    Ported from the original App Engine library:
    http://code.google.com/appengine/docs/python/mail/receivingmail.html

    :copyright: 2010 by tipfy.org.
    :license: Apache Software License, see LICENSE.txt for more details.
"""
from google.appengine.api import mail

from tipfy import RequestHandler


class InboundMailHandler(RequestHandler):
    """Base class for inbound mail handlers. Example::

        # Sub-class overrides receive method.
        class HelloReceiver(InboundMailHandler):

            def receive(self, mail_message):
                logging.info('Received greeting from %s: %s' % (
                    mail_message.sender, mail_message.body))
    """
    def post(self, **kwargs):
        """Transforms body to email request.

        :param kwargs:
            Keyword arguments from the matched URL rule.
        """
        return self.receive(mail.InboundEmailMessage(self.request.data),
            **kwargs)

    def receive(self, mail_message, **kwargs):
        """Receive an email message.

        Override this method to implement an email receiver.

        :param mail_message:
            InboundEmailMessage instance representing received email.
        :param kwargs:
            Keyword arguments from the matched URL rule.
        """
        raise NotImplementedError()
