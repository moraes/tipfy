# -*- coding: utf-8 -*-
"""
    tipfy.ext.jinja2
    ~~~~~~~~~~~~~~~~

    Jinja2 template support for Tipfy.

    Learn more about Jinja2 at http://jinja.pocoo.org/2/

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from jinja2 import Environment, FileSystemLoader, ModuleLoader

from tipfy import Tipfy, import_string, url_for

try:
    from tipfy.ext import i18n
except (ImportError, AttributeError), e:
    i18n = None

#: Default configuration values for this module. Keys are:
#:
#: - ``templates_dir``: Directory for templates. Default is `templates`.
#:
#: - ``templates_compiled_target``: Target for compiled templates. If set,
#:   uses the loader for compiled templates when deployed. If it ends with a
#:   '.zip' it will be treated as a zip file. Default is ``None``.
#:
#: - ``force_use_compiled``: Forces the use of compiled templates even in the
#:   development server.
#:
#: - ``engine_factory``: A function to be called when the template engine is
#:   instantiated, as a string. If ``None``, uses ``create_jinja2_instance()``.
default_config = {
    'templates_dir': 'templates',
    'templates_compiled_target': None,
    'force_use_compiled': False,
    'engine_factory': None,
}


class Jinja2Mixin(object):
    """:class:`tipfy.RequestHandler` mixin that add ``render_template`` and
    ``render_response`` methods to a :class:`tipfy.RequestHandler`. It will
    use the request context to render templates.
    """
    def render_template(self, filename, **context):
        """Renders a template and returns a response object. It will pass

        :param filename:
            The template filename, related to the templates directory.
        :param context:
            Keyword arguments used as variables in the rendered template.
            These will override values set in the request context.
       :return:
            A :class:`tipfy.Response` object with the rendered template.
        """
        request_context = self.request.context.copy()
        request_context.update(context)
        return render_template(filename, **request_context)

    def render_response(self, filename, **context):
        """Returns a response object with a rendered template. It will pass

        :param filename:
            The template filename, related to the templates directory.
        :param context:
            Keyword arguments used as variables in the rendered template.
            These will override values set in the request context.
        :return:
            A :class:`tipfy.Response` object with the rendered template.
        """
        request_context = self.request.context.copy()
        request_context.update(context)
        return render_response(filename, **request_context)


def create_jinja2_instance():
    """Returns the Jinja2 environment.

    :return:
        A ``jinja2.Environment`` instance.
    """
    app = Tipfy.app
    cfg = app.get_config(__name__)
    templates_compiled_target = cfg.get('templates_compiled_target')
    use_compiled = not app.dev or cfg.get( 'force_use_compiled')

    if templates_compiled_target is not None and use_compiled:
        # Use precompiled templates loaded from a module or zip.
        loader = ModuleLoader(templates_compiled_target)
    else:
        # Parse templates for every new environment instances.
        loader = FileSystemLoader(cfg.get( 'templates_dir'))

    if i18n:
        extensions = ['jinja2.ext.i18n']
    else:
        extensions = []

    # Initialize the environment.
    env = Environment(loader=loader, extensions=extensions)

    # Add url_for() by default.
    env.globals['url_for'] = url_for

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

    return env


def get_jinja2_instance():
    """Returns an instance of :class:`Jinja2`, registering it in the WSGI app
    if not yet registered.

    :return:
        An instance of :class:`Jinja2`.
    """
    app = Tipfy.app
    registry = app.registry
    if 'jinja2_instance' not in registry:
        factory_spec = app.get_config(__name__, 'engine_factory')
        if factory_spec:
            if isinstance(factory_spec, basestring):
                factory = import_string(factory_spec)
            else:
                factory = factory_spec
        else:
            factory = create_jinja2_instance

        registry['jinja2_instance'] = factory()

    return registry['jinja2_instance']


def render_template(filename, **context):
    """Renders a template.

    :param filename:
        The template filename, related to the templates directory.
    :param context:
        Keyword arguments used as variables in the rendered template.
    :return:
        A rendered template, in unicode.
    """
    jinja2 = get_jinja2_instance()
    return jinja2.get_template(filename).render(**context)


def render_response(filename, **context):
    """Renders a template and returns a response object.

    :param filename:
        The template filename, related to the templates directory.
    :param context:
        Keyword arguments used as variables in the rendered template.
    :return:
        A :class:`tipfy.Response` object with the rendered template.
    """
    return Tipfy.app.response_class(render_template(filename, **context),
        mimetype='text/html')


def get_template_attribute(filename, attribute):
    """Loads a macro (or variable) a template exports.  This can be used to
    invoke a macro from within Python code.  If you for example have a
    template named `_foo.html` with the following contents:

    .. sourcecode:: html+jinja

       {% macro hello(name) %}Hello {{ name }}!{% endmacro %}

    You can access this from Python code like this::

        hello = get_template_attribute('_foo.html', 'hello')
        return hello('World')

    This function comes from `Flask`.

    :param filename:
        The template filename.
    :param attribute:
        The name of the variable of macro to acccess.
    """
    jinja2 = get_jinja2_instance()
    return getattr(jinja2.get_template(filename).module, attribute)


# Old name.
get_env = get_jinja2_instance
