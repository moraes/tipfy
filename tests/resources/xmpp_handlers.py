from tipfyext.appengine.xmpp import BaseHandler, CommandHandler


class XmppHandler(CommandHandler):
    def foo_command(self, message):
        message.reply('Foo command!')

    def bar_command(self, message):
        message.reply('Bar command!')

    def text_message(self, message):
        super(XmppHandler, self).text_message(message)
        message.reply(message.body)


class XmppHandler2(BaseHandler):
    pass
