# -*- coding: utf-8 -*-
"""
    tipfyext.jinja2
    ~~~~~~~~~~~~~~~

    Jinja2 template support for Tipfy.

    Learn more about Jinja2 at http://jinja.pocoo.org/2/

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import absolute_import

from jinja2 import Environment, FileSystemLoader, ModuleLoader

from werkzeug import cached_property

try:
    from tipfyext import i18n
except ImportError:
    i18n = None

__version__ = '0.1'
__version_info__ = tuple(int(n) for n in __version__.split('.'))

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
default_config = {
    'templates_dir': 'templates',
    'templates_compiled_target': None,
    'force_use_compiled': False,
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
    def __init__(self, app, _globals=None, filters=None, extensions=()):
        self.app = app

        cfg = app.get_config(__name__)
        templates_compiled_target = cfg.get('templates_compiled_target')
        use_compiled = not app.debug or cfg.get('force_use_compiled')

        if templates_compiled_target is not None and use_compiled:
            # Use precompiled templates loaded from a module or zip.
            loader = ModuleLoader(templates_compiled_target)
        else:
            # Parse templates for every new environment instances.
            loader = FileSystemLoader(cfg.get('templates_dir'))

        # Initialize the environment.
        env = Environment(loader=loader, extensions=extensions)

        if _globals:
            env.globals.update(_globals)

        if filters:
            env.filters.update(filters)

        if i18n:
            # Install i18n.
            env.add_extension('jinja2.ext.i18n')
            trans = i18n.get_translations
            env.install_gettext_callables(
                lambda s: trans().ugettext(s),
                lambda s, p, n: trans().ungettext(s, p, n),
                newstyle=True)

            env.globals.update({
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

    @classmethod
    def factory(cls, _app, _name, **kwargs):
        if _name not in _app.registry:
            _app.registry[_name] = cls(_app, **kwargs)

        return _app.registry[_name]
