# -*- coding: utf-8 -*-
"""
    tipfy.ext.jinja2
    ~~~~~~~~~~~~~~~~

    Jinja2 template engine extension.

    Learn more about Jinja2 at http://jinja.pocoo.org/2/

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from os import path
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
from tipfy import local, get_config

#: Default configuration values for this module. Keys are:
#:   - ``templates_dir``: Directory for templates. Default is `templates`.
#:   - ``templates_compiled_dir``: Directory for compiled templates. If None,
#:     don't use compiled templates. Default is ``None``.
default_config = {
    'templates_dir': 'templates',
    'templates_compiled_dir': None,
}

# Jinja2 Environment, cached in the module.
_environment = None


def get_env():
    """Returns the Jinja2 environment, a singleton.

    :return:
        A ``jinja2.Environment`` instance.
    """
    global _environment
    if _environment is None:
        templates_compiled_dir = get_config(__name__, 'templates_compiled_dir')
        if get_config('tipfy', 'dev') or templates_compiled_dir is None:
            # In development, parse templates on every request.
            loader = FileSystemLoader(get_config(__name__, 'templates_dir'))
        else:
            # In production, use precompiled templates loaded from a module.
            loader = ModuleLoader(templates_compiled_dir)

        # Initialize the environment.
        _environment = Environment(loader=loader,
            extensions=['jinja2.ext.i18n'])

        try:
            # Install i18n conditionally.
            _set_i18n(_environment)
        except (ImportError, AttributeError), e:
            # i18n is not available.
            pass

    return _environment


def _set_i18n(environment):
    """Add the internationalization extension to Jinja2 environment."""
    from tipfy.ext.i18n import translations, format_date, format_datetime, \
        format_time
    environment.globals.update({
        'format_date': format_date,
        'format_datetime': format_datetime,
        'format_time': format_time,
    })
    environment.install_gettext_translations(translations)


def render_template(filename, **context):
    """Renders a template.

    :param filename:
        The template filename, related to the templates directory.
    :param context:
        Keyword arguments used as variables in the rendered template.
    :return:
        A rendered template, in unicode.
    """
    return get_env().get_template(filename).render(**context)


def render_response(filename, **context):
    """Renders a template and returns a response object.

    :param filename:
        The template filename, related to the templates directory.
    :param context:
        Keyword arguments used as variables in the rendered template.
    :return:
        A ``werkzeug.Response`` object with the rendered template.
    """
    local.response.data = render_template(filename, **context)
    local.response.mimetype = 'text/html'
    return local.response


class ModuleLoader(object):
    def __init__(self, templatemodule):
        """Loads a pre-compiled template, stored as Python code in a template
        module.

        This loader requires a modification in Jinja2 code (see jinja2.diff).


        The change doesn't affect other loaders, only allows templates to be
        loaded as modules, as described in
        http://dev.pocoo.org/projects/jinja/ticket/349

        `templatemodule`: a single module where compiled templates are stored.
        """
        self.modules = {}
        self.templatemodule = templatemodule

    def load(self, environment, filename, globals=None):
        """Loads a pre-compiled template, stored as Python code in a template
        module.
        """
        if globals is None:
            globals = {}

        # Strip '/' and remove extension.
        filename, ext = path.splitext(filename.strip('/'))

        if filename not in self.modules:
            # Store module to avoid unnecessary repeated imports.
            self.modules[filename] = self.get_module(environment, filename)

        tpl_vars = self.modules[filename].run(environment)

        t = object.__new__(environment.template_class)
        t.environment = environment
        t.globals = globals
        t.name = tpl_vars['name']
        t.filename = filename
        t.blocks = tpl_vars['blocks']

        # render function and module
        t.root_render_func = tpl_vars['root']
        t._module = None

        # debug and loader helpers
        t._debug_info = tpl_vars['debug_info']
        t._uptodate = lambda: True

        return t

    def get_module(self, environment, template):
        # Convert the path to a module name.
        module_name = self.templatemodule + '.' + template.replace('/', '.')
        prefix, obj = module_name.rsplit('.', 1)

        try:
            return getattr(__import__(prefix, None, None, [obj]), obj)
        except (ImportError, AttributeError):
            raise TemplateNotFound(template)
