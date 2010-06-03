# -*- coding: utf-8 -*-
"""
    tipfy.ext.jinja2
    ~~~~~~~~~~~~~~~~

    Jinja2 template engine extension.

    Learn more about Jinja2 at http://jinja.pocoo.org/2/

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import absolute_import
from jinja2 import Environment, FileSystemLoader, ModuleLoader

from tipfy import get_config, url_for, Response

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
            A :class:`tipfy.Response` object with the rendered template.
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
            # Use precompiled templates loaded from a module or zip.
            loader = ModuleLoader(templates_compiled_target)
        else:
            # Parse templates for every new environment instances.
            loader = FileSystemLoader(get_config(__name__, 'templates_dir'))

        # Initialize the environment.
        _environment = Environment(loader=loader,
            extensions=['jinja2.ext.i18n'])

        # Add url_for() by default.
        _environment.globals['url_for'] = url_for

        try:
            from tipfy.ext import i18n
            # Install i18n, first forcing it to be loaded if not yet.
            i18n.get_translations()
            _environment.install_gettext_translations(i18n.translations)
            _environment.globals.update({
                'format_date':     i18n.format_date,
                'format_time':     i18n.format_time,
                'format_datetime': i18n.format_datetime,
            })
        except (ImportError, AttributeError), e:
            pass

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
        A :class:`tipfy.Response` object with the rendered template.
    """
    return Response(render_template(filename, **context), mimetype='text/html')


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
    return getattr(get_env().get_template(filename).module, attribute)


def compile_templates(argv=None):
    """Compiles templates for better performance. This is a command line
    script. From the buildout directory, run:

        bin/jinja2_compile

    It will compile templates from the directory configured for 'templates_dir'
    to the one configured for 'templates_compiled_target'.

    At this time it doesn't accept any arguments.
    """
    import os
    import sys

    if argv is None:
        argv = sys.argv

    cwd = os.getcwd()
    app_path = os.path.join(cwd, 'app')
    gae_path = os.path.join(cwd, 'etc/parts/google_appengine')

    extra_paths = [
        app_path,
        gae_path,
        # These paths are required by the SDK.
        os.path.join(gae_path, 'lib', 'antlr3'),
        os.path.join(gae_path, 'lib', 'django'),
        os.path.join(gae_path, 'lib', 'ipaddr'),
        os.path.join(gae_path, 'lib', 'webob'),
        os.path.join(gae_path, 'lib', 'yaml', 'lib'),
    ]

    sys.path = extra_paths + sys.path

    from config import config
    from tipfy import make_wsgi_app

    def logger(msg):
        sys.stderr.write('\n%s\n' % msg)

    def filter_templates(tpl):
        # Only ignore templates that start with '.'.
        return not os.path.basename(tpl).startswith('.')

    app = make_wsgi_app(config)
    template_path = get_config('tipfy.ext.jinja2', 'templates_dir')
    compiled_path = get_config('tipfy.ext.jinja2', 'templates_compiled_target')

    if compiled_path is None:
        raise ValueError('Missing configuration key to compile templates.')

    if isinstance(template_path, basestring):
        # A single path.
        source = os.path.join(app_path, template_path)
    else:
        # A list of paths.
        source = [os.path.join(app_path, p) for p in template_path]

    target = os.path.join(app_path, compiled_path)

    # Set templates dir and deactivate compiled dir to use normal loader to
    # find the templates to be compiled.
    app.config['tipfy.ext.jinja2']['templates_dir'] = source
    app.config['tipfy.ext.jinja2']['templates_compiled_target'] = None

    if target.endswith('.zip'):
        zip_cfg = 'deflated'
    else:
        zip_cfg = None

    def walk(top, topdown=True, onerror=None, followlinks=False):
        from os.path import join, isdir, islink
        try:
            names = os.listdir(top)
        except os.error, err:
            if onerror is not None:
                onerror(err)
            return

        dirs, nondirs = [], []
        for name in names:
            if isdir(join(top, name)):
                dirs.append(name)
            else:
                nondirs.append(name)

        if topdown:
            yield top, dirs, nondirs
        for name in dirs:
            path = join(top, name)
            if followlinks or not islink(path):
                for x in walk(path, topdown, onerror, followlinks):
                    yield x
        if not topdown:
            yield top, dirs, nondirs

    # Set it to follow symlinks.
    def list_templates(self):
        found = set()
        for searchpath in self.searchpath:
            for dirpath, dirnames, filenames in walk(searchpath,
                followlinks=True):
                for filename in filenames:
                    template = os.path.join(dirpath, filename) \
                        [len(searchpath):].strip(os.path.sep) \
                                          .replace(os.path.sep, '/')
                    if template[:2] == './':
                        template = template[2:]
                    if template not in found:
                        found.add(template)
        return sorted(found)

    FileSystemLoader.list_templates = list_templates

    env = get_env()
    env.compile_templates(target, extensions=None, filter_func=filter_templates,
                          zip=zip_cfg, log_function=logger,
                          ignore_errors=False, py_compile=False)
