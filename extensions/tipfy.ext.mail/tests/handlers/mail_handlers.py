from tipfy.ext.mail import InboundMailHandler


class MailHandler(InboundMailHandler):
    def receive(self, mail_message, **kwargs):
        for content_type, body in mail_message.bodies('text/plain'):
            decoded = body.decode()
            if decoded:
                return decoded

        return ''


class MailHandler2(InboundMailHandler):
    pass
