from __future__ import division
from jinja2.runtime import LoopContext, TemplateReference, Macro, Markup, TemplateRuntimeError, missing, concat, escape, markup_join, unicode_join, to_string, TemplateNotFound
name = 'dump_object.html'

def root(context):
    l_items = context.resolve('items')
    l_repr = context.resolve('repr')
    l_title = context.resolve('title')
    t_1 = environment.filters['e']
    if 0: yield None
    yield u'<div class="box">\n  <h3>%s</h3>\n  ' % (
        t_1(l_title), 
    )
    if l_repr:
        if 0: yield None
        yield u'\n    <div class="repr">%s</div>\n  ' % (
            l_repr, 
        )
    yield u'\n  <table>\n  '
    l_value = l_key = missing
    for (l_key, l_value) in l_items:
        if 0: yield None
        yield u'\n    <tr>\n      <th>%s</th>\n      <td>%s</td>\n    </tr>\n  ' % (
            t_1(l_key), 
            l_value, 
        )
    l_value = l_key = missing
    yield u'\n  </table>\n</div>'

blocks = {}
debug_info = '1=11&2=12&3=14&4=17&5=19&7=21&9=24&10=25&12=28'