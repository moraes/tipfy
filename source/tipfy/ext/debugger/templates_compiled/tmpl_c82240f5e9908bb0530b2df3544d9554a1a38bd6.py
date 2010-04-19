from __future__ import division
from jinja2.runtime import LoopContext, TemplateReference, Macro, Markup, TemplateRuntimeError, missing, concat, escape, markup_join, unicode_join, to_string, TemplateNotFound
name = 'traceback_summary.html'

def root(context):
    l_include_title = context.resolve('include_title')
    l_traceback = context.resolve('traceback')
    t_1 = environment.filters['e']
    if 0: yield None
    yield u'<div class="traceback">\n  '
    if environment.getattr(l_traceback, 'is_syntax_error'):
        if 0: yield None
        yield u'\n    '
        if l_include_title:
            if 0: yield None
            yield u'\n      <h3>Syntax Error</h3>\n    '
        yield u'\n    <ul>\n    '
        l_frame = missing
        for l_frame in environment.getattr(l_traceback, 'frames'):
            if 0: yield None
            yield u'\n      <li>%s</li>\n    ' % (
                context.call(environment.getattr(l_frame, 'render')), 
            )
        l_frame = missing
        yield u'\n    </ul>\n    <pre>%s</pre>\n  ' % (
            t_1(environment.getattr(l_traceback, 'exception')), 
        )
    else:
        if 0: yield None
        yield u'\n    '
        if l_include_title:
            if 0: yield None
            yield u'\n      <h3>Traceback <em>(most recent call last)</em>:</h3>\n    '
        yield u'\n    <ul>\n    '
        l_frame = missing
        for l_frame in environment.getattr(l_traceback, 'frames'):
            if 0: yield None
            yield u'\n      <li'
            if environment.getattr(l_frame, 'info'):
                if 0: yield None
                yield u' title="%s"' % (
                    t_1(environment.getattr(l_frame, 'info')), 
                )
            yield u'>%s</li>\n    ' % (
                context.call(environment.getattr(l_frame, 'render')), 
            )
        l_frame = missing
        yield u'\n    </ul>\n    <blockquote>%s</blockquote>\n  ' % (
            t_1(environment.getattr(l_traceback, 'exception')), 
        )
    yield u'\n</div>'

blocks = {}
debug_info = '1=10&2=11&3=14&5=17&7=19&8=22&9=25&11=26&12=30&13=31&15=34&17=36&18=39&19=48&21=49&22=51'