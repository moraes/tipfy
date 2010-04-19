from __future__ import division
from jinja2.runtime import LoopContext, TemplateReference, Macro, Markup, TemplateRuntimeError, missing, concat, escape, markup_join, unicode_join, to_string, TemplateNotFound
name = 'source.html'

def root(context):
    l_lines = context.resolve('lines')
    t_1 = environment.filters['e']
    if 0: yield None
    yield u'<table class="source">\n'
    l_line = missing
    for l_line in l_lines:
        if 0: yield None
        yield u'\n  <tr class="%s">\n    <td class="lineno">%s</td>\n    <td>%s</td>\n  </tr>\n' % (
            context.call(environment.getattr(' ', 'join'), environment.getattr(l_line, 'classes')), 
            environment.getattr(l_line, 'lineno'), 
            t_1(environment.getattr(l_line, 'code')), 
        )
    l_line = missing
    yield u'\n</table>'

blocks = {}
debug_info = '1=9&2=11&3=14&4=15&5=16&7=19'