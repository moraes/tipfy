# -*- coding: utf-8 -*-
"""
    tipfy.ext.jinja2.patch
    ~~~~~~~~~~~~~~~~~~~~~~

    Monkey patches for Jinja2 to work with templates precompiled as Python
    modules.

    See http://dev.pocoo.org/projects/jinja/ticket/349

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from jinja2 import Template
from jinja2.compiler import CodeGenerator, nodes, Frame, find_undeclared


def from_code(cls, environment, code, globals, uptodate=None):
    """Creates a template object from compiled code and the globals.  This
    is used by the loaders and environment to create a template object.
    """
    t = object.__new__(cls)
    # PATCH: don't include environment in namespace, instead inject it in run().
    namespace = {
        '__jinja_template__':   t
    }
    exec code in namespace

    tpl_vars = namespace['run'](environment)
    t.environment = environment
    t.globals = globals
    t.name = tpl_vars['name']
    t.filename = code.co_filename
    t.blocks = tpl_vars['blocks']

    # render function and module
    t.root_render_func = tpl_vars['root']
    t._module = None

    # debug and loader helpers
    t._debug_info = tpl_vars['debug_info']
    t._uptodate = uptodate

    return t
    # End of PATCH.


def visit_Template(self, node, frame=None):
    assert frame is None, 'no root frame allowed'
    from jinja2.runtime import __all__ as exported
    self.writeline('from __future__ import division')
    self.writeline('from jinja2.runtime import ' + ', '.join(exported))

    # PATCH: add a run() function to inject environment.
    self.writeline('def run(environment):')
    self.indent()
    # End of PATCH.

    # do we have an extends tag at all?  If not, we can save some
    # overhead by just not processing any inheritance code.
    have_extends = node.find(nodes.Extends) is not None

    # find all blocks
    for block in node.find_all(nodes.Block):
        if block.name in self.blocks:
            self.fail('block %r defined twice' % block.name, block.lineno)
        self.blocks[block.name] = block

    # find all imports and import them
    for import_ in node.find_all(nodes.ImportedName):
        if import_.importname not in self.import_aliases:
            imp = import_.importname
            self.import_aliases[imp] = alias = self.temporary_identifier()
            if '.' in imp:
                module, obj = imp.rsplit('.', 1)
                self.writeline('from %s import %s as %s' %
                               (module, obj, alias))
            else:
                self.writeline('import %s as %s' % (imp, alias))

    # add the load name
    self.writeline('name = %r' % self.name)

    # generate the root render function.
    self.writeline('def root(context, environment=environment):', extra=1)

    # process the root
    frame = Frame()
    frame.inspect(node.body)
    frame.toplevel = frame.rootlevel = True
    frame.require_output_check = have_extends and not self.has_known_extends
    self.indent()
    if have_extends:
        self.writeline('parent_template = None')
    if 'self' in find_undeclared(node.body, ('self',)):
        frame.identifiers.add_special('self')
        self.writeline('l_self = TemplateReference(context)')
    self.pull_locals(frame)
    self.pull_dependencies(node.body)
    self.blockvisit(node.body, frame)
    self.outdent()

    # make sure that the parent root is called.
    if have_extends:
        if not self.has_known_extends:
            self.indent()
            self.writeline('if parent_template is not None:')
        self.indent()
        self.writeline('for event in parent_template.'
                       'root_render_func(context):')
        self.indent()
        self.writeline('yield event')
        self.outdent(2 + (not self.has_known_extends))

    # at this point we now have the blocks collected and can visit them too.
    for name, block in self.blocks.iteritems():
        block_frame = Frame()
        block_frame.inspect(block.body)
        block_frame.block = name
        self.writeline('def block_%s(context, environment=environment):'
                       % name, block, 1)
        self.indent()
        undeclared = find_undeclared(block.body, ('self', 'super'))
        if 'self' in undeclared:
            block_frame.identifiers.add_special('self')
            self.writeline('l_self = TemplateReference(context)')
        if 'super' in undeclared:
            block_frame.identifiers.add_special('super')
            self.writeline('l_super = context.super(%r, '
                           'block_%s)' % (name, name))
        self.pull_locals(block_frame)
        self.pull_dependencies(block.body)
        self.blockvisit(block.body, block_frame)
        self.outdent()

    self.writeline('blocks = {%s}' % ', '.join('%r: block_%s' % (x, x)
                                               for x in self.blocks),
                   extra=1)

    # add a function that returns the debug info
    self.writeline('debug_info = %r' % '&'.join('%s=%s' % x for x
                                                in self.debug_info))

    # PATCH: return local variables and outdent run().
    self.writeline('return locals()')
    self.outdent()
    # End of PATCH.


# Apply the patches.
Template.from_code = from_code
CodeGenerator.visit_Template = visit_Template
