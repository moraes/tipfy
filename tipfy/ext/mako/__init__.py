# -*- coding: utf-8 -*-
"""
    tipfy.ext.mako
    ~~~~~~~~~~~~~~

    Mako template engine extension.

    It requires the mako module to be added to the lib dir. Mako can be
    downloaded at http://www.makotemplates.org/

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from os import path
from mako.lookup import TemplateLookup
from mako.runtime import Context
from StringIO import StringIO

from tipfy import local, get_config, Response

#: Default configuration values for this module. Keys are:
#:
#: - ``templates_dir``: Directory for templates. Default is `templates`.
default_config = {
    'templates_dir': 'templates',
}

# TemplateLookup cached in the module.
_lookup = None


class MakoMixin(object):
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


def get_lookup():
    global _lookup
    if _lookup is None:
        _lookup = TemplateLookup(directories=[path.join(get_config(__name__,
            'templates_dir'))], output_encoding='utf-8',
            encoding_errors='replace')

    return _lookup


def render_template(filename, **context):
    """Renders a template.

    :param filename:
        The template filename, related to the templates directory.
    :param context:
        Keyword arguments used as variables in the rendered template.
    :return:
        A rendered template, in unicode.
    """
    template = get_lookup().get_template(filename)
    buf = StringIO()
    template.render_context(Context(buf, **context))
    return buf.getvalue()


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
