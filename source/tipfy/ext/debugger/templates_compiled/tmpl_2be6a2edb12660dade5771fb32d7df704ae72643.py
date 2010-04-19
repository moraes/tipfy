from __future__ import division
from jinja2.runtime import LoopContext, TemplateReference, Macro, Markup, TemplateRuntimeError, missing, concat, escape, markup_join, unicode_join, to_string, TemplateNotFound
name = 'traceback_full.html'

def root(context):
    l_traceback = context.resolve('traceback')
    l_evalex = context.resolve('evalex')
    t_1 = environment.filters['e']
    if 0: yield None
    yield u'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\n  "http://www.w3.org/TR/html4/loose.dtd">\n<html>\n  <head>\n    <title>%s // Werkzeug Debugger</title>\n    <link rel="stylesheet" href="./__debugger__?cmd=resource&amp;f=style.css" type="text/css">\n    <script type="text/javascript" src="./__debugger__?cmd=resource&amp;f=jquery.js"></script>\n    <script type="text/javascript" src="./__debugger__?cmd=resource&amp;f=debugger.js"></script>\n    <script type="text/javascript">\n    var TRACEBACK = %s,\n          CONSOLE_MODE = false,\n          EVALEX = ' % (
        t_1(environment.getattr(l_traceback, 'exception')), 
        environment.getattr(l_traceback, 'id'), 
    )
    if l_evalex:
        if 0: yield None
        yield u"'true'"
    else:
        if 0: yield None
        yield u"'false'"
    yield u';\n    </script>\n  </head>\n  <body>\n    <div class="debugger">\n      <h1>%s</h1>\n      <div class="detail">\n        <p class="errormsg">%s</p>\n      </div>\n      <h2 class="traceback">Traceback <em>(most recent call last)</em></h2>\n      %s\n      <div class="plain">\n        <form action="http://paste.pocoo.org/" method="post">\n          <p>\n            <input type="hidden" name="language" value="pytb">\n            This is the Copy/Paste friendly version of the traceback.  <span\n            class="pastemessage">You can also paste this traceback into the public\n            lodgeit pastebin: <input type="submit" value="create paste"></span>\n          </p>\n          <textarea cols="50" rows="10" name="code" readonly>%s</textarea>\n        </form>\n      </div>\n      <div class="explanation">\n        The debugger caught an exception in your WSGI application.  You can now\n        look at the traceback which lead to the error.  <span class="nojavascript">\n        If you enable JavaScript you can also use additional features such as code\n        execution (if the evalex feature is enabled), automatic pasting of the\n        exceptions and much more.</span>\n      </div>\n      <div class="footer">\n        Brought to you by <strong class="arthur">DON\'T PANIC</strong>, your\n        friendly Werkzeug powered traceback interpreter.\n      </div>\n    </div>\n  </body>\n</html>\n<!--\n\n%s\n\n-->' % (
        t_1(environment.getattr(l_traceback, 'exception_type')), 
        t_1(environment.getattr(l_traceback, 'exception')), 
        context.call(environment.getattr(l_traceback, 'render_summary'), include_title=False), 
        t_1(environment.getattr(l_traceback, 'plaintext')), 
        environment.getattr(l_traceback, 'plaintext'), 
    )

blocks = {}
debug_info = '1=10&5=11&10=12&12=14&17=21&19=22&22=23&31=24&50=25'