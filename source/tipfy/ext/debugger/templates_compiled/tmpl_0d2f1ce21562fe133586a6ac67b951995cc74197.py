from __future__ import division
from jinja2.runtime import LoopContext, TemplateReference, Macro, Markup, TemplateRuntimeError, missing, concat, escape, markup_join, unicode_join, to_string, TemplateNotFound
name = 'help_command.html'

def root(context):
    l_text = context.resolve('text')
    l_title = context.resolve('title')
    if 0: yield None
    yield u'<%%py missing = object() %%>\n<div class="box">\n  <%% if title and text %%>\n    <h3>%s</h3>\n    <pre class="help">%s</pre>\n  <%% else %%>\n    <h3>Help</h3>\n    <p>Type help(object) for help about object.</p>\n  <%% endif %%>\n</div>' % (
        l_title, 
        l_text, 
    )

blocks = {}
debug_info = '1=9&4=10&5=11'