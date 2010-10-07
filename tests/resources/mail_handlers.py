from tipfy import Response

from tipfy.appengine.mail import InboundMailHandler


class MailHandler(InboundMailHandler):
    def receive(self, mail_message, **kwargs):
        for content_type, body in mail_message.bodies('text/plain'):
            decoded = body.decode()
            if decoded:
                return Response(decoded)

        return Response('')


class MailHandler2(InboundMailHandler):
    pass
