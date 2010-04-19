from __future__ import division
from jinja2.runtime import LoopContext, TemplateReference, Macro, Markup, TemplateRuntimeError, missing, concat, escape, markup_join, unicode_join, to_string, TemplateNotFound
name = 'console.html'

def root(context):
    if 0: yield None
    yield u'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\n  "http://www.w3.org/TR/html4/loose.dtd">\n<html>\n  <head>\n    <title>Console // Werkzeug Debugger</title>\n    <link rel="stylesheet" href="./__debugger__?cmd=resource&amp;f=style.css" type="text/css">\n    <script type="text/javascript" src="./__debugger__?cmd=resource&amp;f=jquery.js"></script>\n    <script type="text/javascript" src="./__debugger__?cmd=resource&amp;f=debugger.js"></script>\n    <script type="text/javascript">\n      var EVALEX = true,\n          CONSOLE_MODE = true;\n    </script>\n  </head>\n  <body>\n    <div class="debugger">\n      <h1>Interactive Console</h1>\n      <div class="explanation">\n        In this console you can execute Python expressions in the context of the\n        application.  The initial namespace was created by the debugger automatically.\n      </div>\n      <div class="console"><div class="inner">The Console requires JavaScript.</div></div>\n      <div class="footer">\n        Brought to you by <strong class="arthur">DON\'T PANIC</strong>, your\n        friendly Werkzeug powered traceback interpreter.\n      </div>\n    </div>\n  </body>\n</html>'

blocks = {}
debug_info = '1=7'