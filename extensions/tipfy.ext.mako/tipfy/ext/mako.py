# -*- coding: utf-8 -*-
"""
    tipfy.ext.mako
    ~~~~~~~~~~~~~~

    Mako template support for Tipfy.

    Learn more about Mako at http://www.makotemplates.org/

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import absolute_import
from cStringIO import StringIO

from mako.lookup import TemplateLookup
from mako.runtime import Context

from tipfy import Tipfy, get_config

#: Default configuration values for this module. Keys are:
#:
#: - ``templates_dir``: Directory for templates. Default is `templates`.
default_config = {
    'templates_dir': 'templates',
}


class MakoMixin(object):
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
        request_context = dict(self.request.context)
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
        request_context = dict(self.request.context)
        request_context.update(context)
        return render_response(filename, **request_context)


def get_mako_instance():
    """Returns an instance of ``mako.lookup.TemplateLookup``, registering it
    in the WSGI app if not yet registered.

    :return:
        An instance of ``mako.lookup.TemplateLookup``.
    """
    registry = Tipfy.app.registry
    if 'mako_instance' not in registry:
        dirs = get_config(__name__, 'templates_dir')
        if isinstance(dirs, basestring):
            dirs = [dirs]

        registry['mako_instance'] = TemplateLookup(directories=dirs,
            output_encoding='utf-8', encoding_errors='replace')

    return registry['mako_instance']


def render_template(filename, **context):
    """Renders a template.

    :param filename:
        The template filename, related to the templates directory.
    :param context:
        Keyword arguments used as variables in the rendered template.
    :return:
        A rendered template, in unicode.
    """
    template = get_mako_instance().get_template(filename)
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
        A :class:`tipfy.Response` object with the rendered template.
    """
    return Tipfy.app.response_class(render_template(filename, **context),
        mimetype='text/html')


# Old name.
get_lookup = get_mako_instance
