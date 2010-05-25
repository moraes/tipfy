from tipfy.ext.xmpp import CommandHandler

class XmppHandler(CommandHandler):
    def foo_command(self, message):
        message.reply('Foo command!')

    def bar_command(self, message):
        message.reply('Bar command!')
