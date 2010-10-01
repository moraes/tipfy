# -*- coding: utf-8 -*-
"""
    tipfyext.jinja2
    ~~~~~~~~~~~~~~~

    Jinja2 template support for Tipfy.

    Learn more about Jinja2 at http://jinja.pocoo.org/2/

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from jinja2 import Environment, FileSystemLoader, ModuleLoader

from werkzeug import cached_property

#: Default configuration values for this module. Keys are:
#:
#: templates_dir
#:     Directory for templates. Default is `templates`.
#:
#: templates_compiled_target
#:     Target for compiled templates. If set, uses the loader for compiled
#:     templates when deployed. If it ends with a '.zip' it will be treated
#:     as a zip file. Default is None.
#:
#: force_use_compiled
#:     Forces the use of compiled templates even in the development server.
#:
#: environment_args
#:     Keyword arguments used to instantiate the Jinja2 environment. By
#:     default autoescaping is enabled and two extensions are set:
#:     'jinja2.ext.autoescape' and 'jinja2.ext.with_'.
default_config = {
    'templates_dir': 'templates',
    'templates_compiled_target': None,
    'force_use_compiled': False,
    'environment_args': dict(
        autoescape=True,
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_'],
    ),
}


class Jinja2Mixin(object):
    """Mixin that adds ``render_template`` and ``render_response`` methods
    to a :class:`tipfy.RequestHandler`. It will use the request context to
    render templates.
    """
    @cached_property
    def jinja2(self):
        return Jinja2.factory(self.app, 'jinja2')

    def render_template(self, _filename, **context):
        return self.jinja2.render_template(_filename, **context)

    def render_response(self, _filename, **context):
        return self.jinja2.render_response(_filename, **context)


class Jinja2(object):
    def __init__(self, app, _globals=None, filters=None):
        self.app = app
        config = app.config[__name__]
        kwargs = config['environment_args'] or {}
        enable_i18n = 'jinja2.ext.i18n' in kwargs.get('extensions', [])

        if not kwargs.get('loader'):
            templates_compiled_target = config['templates_compiled_target']
            use_compiled = not app.debug or config['force_use_compiled']

            if templates_compiled_target is not None and use_compiled:
                # Use precompiled templates loaded from a module or zip.
                kwargs['loader'] = ModuleLoader(templates_compiled_target)
            else:
                # Parse templates for every new environment instances.
                kwargs['loader'] = FileSystemLoader(config['templates_dir'])

        # Initialize the environment.
        env = Environment(**kwargs)

        if _globals:
            env.globals.update(_globals)

        if filters:
            env.filters.update(filters)

        if enable_i18n:
            # Install i18n.
            from tipfy import i18n
            env.install_gettext_callables(
                lambda s: i18n.gettext(s),
                lambda s, p, n: i18n.ngettext(s, p, n),
                newstyle=True)
            env.filters.update({
                'format_date':     i18n.format_date,
                'format_time':     i18n.format_time,
                'format_datetime': i18n.format_datetime,
            })

        env.globals['url_for'] = app.url_for
        self.environment = env

    def render(self, _filename, **context):
        """Renders a template and returns a response object.

        :param _filename:
            The template filename, related to the templates directory.
        :param context:
            Keyword arguments used as variables in the rendered template.
            These will override values set in the request context.
       :returns:
            A rendered template.
        """
        return self.environment.get_template(_filename).render(**context)

    def render_template(self, _filename, **context):
        """Renders a template and returns a response object.

        :param _filename:
            The template filename, related to the templates directory.
        :param context:
            Keyword arguments used as variables in the rendered template.
            These will override values set in the request context.
       :returns:
            A rendered template.
        """
        ctx = self.app.request.context.copy()
        ctx.update(context)
        return self.render(_filename, **ctx)

    def render_response(self, _filename, **context):
        """Returns a response object with a rendered template.

        :param _filename:
            The template filename, related to the templates directory.
        :param context:
            Keyword arguments used as variables in the rendered template.
            These will override values set in the request context.
        """
        res = self.render_template(_filename, **context)
        return self.app.response_class(res)

    def get_template_attribute(self, filename, attribute):
        """Loads a macro (or variable) a template exports.  This can be used to
        invoke a macro from within Python code.  If you for example have a
        template named `_foo.html` with the following contents:

        .. sourcecode:: html+jinja

           {% macro hello(name) %}Hello {{ name }}!{% endmacro %}

        You can access this from Python code like this::

            hello = get_template_attribute('_foo.html', 'hello')
            return hello('World')

        This function is borrowed from `Flask`.

        :param filename:
            The template filename.
        :param attribute:
            The name of the variable of macro to acccess.
        """
        template = self.environment.get_template(filename)
        return getattr(template.module, attribute)

    @classmethod
    def factory(cls, _app, _name, **kwargs):
        if _name not in _app.registry:
            _app.registry[_name] = cls(_app, **kwargs)

        return _app.registry[_name]
