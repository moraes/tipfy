# -*- coding: utf-8 -*-
"""
    tipfy.ext.jinja2
    ~~~~~~~~~~~~~~~~

    Jinja2 template engine extension.

    Learn more about Jinja2 at http://jinja.pocoo.org/2/

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from jinja2 import Environment, FileSystemLoader, ModuleLoader

from tipfy import local, get_config, url_for, Response
from tipfy.ext import i18n

#: Default configuration values for this module. Keys are:
#:
#: - ``templates_dir``: Directory for templates. Default is `templates`.
#:
#:   - ``templates_compiled_target``: Target for compiled templates. If set,
#:     uses the loader for compiled templates when deployed. If it ends with a
#:     '.zip' it will be treated as a zip file. Default is ``None``.
#:
#: - ``force_use_compiled``: Forces the use of compiled templates even in the
#:   development server
default_config = {
    'templates_dir': 'templates',
    'templates_compiled_target': None,
    'force_use_compiled': False,
}

# Jinja2 Environment, cached in the module.
_environment = None


class Jinja2Mixin(object):
    """:class:`tipfy.RequestHandler` mixing to add a convenient
    ``render_response`` function to handlers. It expects a ``context``
    dictionary to be set in the handler, so that the passed values are added to
    the context. The idea is that other mixins can use this context to set
    template values.
    """
    def render_response(self, filename, **values):
        """Renders a template and returns a response object.

        :param filename:
            The template filename, related to the templates directory.
        :param context:
            Keyword arguments used as variables in the rendered template.
        :return:
            A ``werkzeug.Response`` object with the rendered template.
        """
        context = dict(self.context)
        context.update(values)
        return render_response(filename, **context)


def get_env():
    """Returns the Jinja2 environment, a singleton.

    :return:
        A ``jinja2.Environment`` instance.
    """
    global _environment
    if _environment is None:
        templates_compiled_target = get_config(__name__,
            'templates_compiled_target')

        use_compiled = not get_config('tipfy', 'dev') or get_config(__name__,
            'force_use_compiled')

        if templates_compiled_target is not None and use_compiled:
            # Use precompiled templates loaded from a module.
            loader = ModuleLoader(templates_compiled_target)
        else:
            # Parse templates on every request.
            loader = FileSystemLoader(get_config(__name__, 'templates_dir'))

        # Initialize the environment.
        _environment = Environment(loader=loader,
            extensions=['jinja2.ext.i18n'])

        # Add url_for() by default.
        _environment.globals.update({
            'url_for':         url_for,
            'format_date':     i18n.format_date,
            'format_time':     i18n.format_time,
            'format_datetime': i18n.format_datetime,
        })

        # Install i18n, first forcing it to be loaded if not yet.
        i18n.get_translations()
        _environment.install_gettext_translations(i18n.translations)

    return _environment


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
    return Response(render_template(filename, **context), mimetype='text/html')
