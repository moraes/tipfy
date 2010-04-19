from __future__ import division
from jinja2.runtime import LoopContext, TemplateReference, Macro, Markup, TemplateRuntimeError, missing, concat, escape, markup_join, unicode_join, to_string, TemplateNotFound
name = 'traceback_plaintext.html'

def root(context):
    l_traceback = context.resolve('traceback')
    if 0: yield None
    yield u'Traceback (most recent call last):\n'
    l_frame = missing
    for l_frame in environment.getattr(l_traceback, 'frames'):
        if 0: yield None
        yield u'\n  File "%s", line %s, in %s\n    %s\n' % (
            environment.getattr(l_frame, 'filename'), 
            environment.getattr(l_frame, 'lineno'), 
            environment.getattr(l_frame, 'function_name'), 
            context.call(environment.getattr(environment.getattr(l_frame, 'current_line'), 'strip')), 
        )
    l_frame = missing
    yield u'\n'
    yield to_string(environment.getattr(l_traceback, 'exception'))

blocks = {}
debug_info = '1=8&2=10&3=13&4=16&5=19&6=20'