# -*- coding: utf-8 -*-
"""
    tipfy.ext.jinja2
    ~~~~~~~~~~~~~~~~

    Jinja2 template support for Tipfy.

    Learn more about Jinja2 at http://jinja.pocoo.org/2/

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import absolute_import

from jinja2 import Environment, FileSystemLoader, ModuleLoader

from tipfy import Tipfy

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

_INSTANCE = None


class Jinja2(object):
    """:class:`tipfy.RequestHandler` mixin that add ``render_template`` and
    ``render_response`` methods to a :class:`tipfy.RequestHandler`. It will
    use the request context to render templates.
    """
    def __init__(self, app, globals=None, filters=None, extensions=None):
        self.app = app
        self.globals = globals
        self.filters = filters
        self.extensions = extensions
        self.environment = None

    def create_environment(self):
        cfg = self.app.get_config(__name__)
        templates_compiled_target = cfg.get('templates_compiled_target')
        use_compiled = not self.app.debug or cfg.get('force_use_compiled')

        if templates_compiled_target is not None and use_compiled:
            # Use precompiled templates loaded from a module or zip.
            loader = ModuleLoader(templates_compiled_target)
        else:
            # Parse templates for every new environment instances.
            loader = FileSystemLoader(cfg.get('templates_dir'))

        extensions = []
        if i18n:
            extensions.append('jinja2.ext.i18n')

        # Initialize the environment.
        env = Environment(loader=loader, extensions=extensions)

        if i18n:
            # Install i18n.
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

        env.globals['url_for'] = self.app.url_for

        self.environment = env
        return env

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
        environment = self.environment or self.create_environment()
        return environment.get_template(_filename).render(**context)

    def render_with_context(self, _filename, **context):
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
        res = self.render_with_context(_filename, **context)
        return self.app.response_class(res)

    @classmethod
    def factory(cls, _app, _name, **kwargs):
        if _name not in _app.registry:
            _app.registry[_name] = cls(_app, **kwargs)

        return _app.registry[_name]


def get_jinja2(*args, **kwargs):
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = Jinja2(Tipfy.app, *args, **kwargs)

    return _INSTANCE
