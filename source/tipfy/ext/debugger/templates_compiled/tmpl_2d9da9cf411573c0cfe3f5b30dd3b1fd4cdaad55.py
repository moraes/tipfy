from __future__ import division
from jinja2.runtime import LoopContext, TemplateReference, Macro, Markup, TemplateRuntimeError, missing, concat, escape, markup_join, unicode_join, to_string, TemplateNotFound
name = 'frame.html'

def root(context):
    l_frame = context.resolve('frame')
    t_1 = environment.filters['e']
    if 0: yield None
    yield u'<div class="frame" id="frame-%s">\n  <h4>File <cite>"%s"</cite>, line <em>%s</em>,\n      in <code>%s</code></h4>\n  <pre>%s</pre>\n</div>' % (
        environment.getattr(l_frame, 'id'), 
        t_1(environment.getattr(l_frame, 'filename')), 
        environment.getattr(l_frame, 'lineno'), 
        t_1(environment.getattr(l_frame, 'function_name')), 
        t_1(context.call(environment.getattr(environment.getattr(l_frame, 'current_line'), 'strip'))), 
    )

blocks = {}
debug_info = '1=9&2=11&3=13&4=14'