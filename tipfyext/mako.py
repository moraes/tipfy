# -*- coding: utf-8 -*-
"""
    tipfyext.mako
    ~~~~~~~~~~~~~

    Mako template support for Tipfy.

    Learn more about Mako at http://www.makotemplates.org/

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import absolute_import
from cStringIO import StringIO

from mako.lookup import TemplateLookup
from mako.runtime import Context

from werkzeug import cached_property

#: Default configuration values for this module. Keys are:
#:
#: templates_dir
#:     Directory for templates. Default is `templates`.
default_config = {
    'templates_dir': 'templates',
}


class Mako(object):
    def __init__(self, app, _globals=None, filters=None):
        self.app = app
        config = app.config[__name__]
        dirs = config.get('templates_dir')
        if isinstance(dirs, basestring):
            dirs = [dirs]

        self.environment = TemplateLookup(directories=dirs,
            output_encoding='utf-8', encoding_errors='replace')

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
        template = self.environment.get_template(_filename)
        buf = StringIO()
        template.render_context(Context(buf, **context))
        return buf.getvalue()

    def render_template(self, _handler, _filename, **context):
        """Renders a template and returns a response object.

        :param _filename:
            The template filename, related to the templates directory.
        :param context:
            Keyword arguments used as variables in the rendered template.
            These will override values set in the request context.
       :returns:
            A rendered template.
        """
        ctx = _handler.context.copy()
        ctx.update(context)
        return self.render(_filename, **ctx)

    def render_response(self, _handler, _filename, **context):
        """Returns a response object with a rendered template.

        :param _filename:
            The template filename, related to the templates directory.
        :param context:
            Keyword arguments used as variables in the rendered template.
            These will override values set in the request context.
        """
        res = self.render_template(_handler, _filename, **context)
        return self.app.response_class(res)

    @classmethod
    def factory(cls, _app, _name, **kwargs):
        if _name not in _app.registry:
            _app.registry[_name] = cls(_app, **kwargs)

        return _app.registry[_name]


class MakoMixin(object):
    """Mixin that adds ``render_template`` and ``render_response`` methods
    to a :class:`tipfy.RequestHandler`. It will use the request context to
    render templates.
    """
    # The Mako creator.
    mako_class = Mako

    @cached_property
    def mako(self):
        return self.mako_class.factory(self.app, 'mako')

    def render_template(self, _filename, **context):
        return self.mako.render_template(self, _filename, **context)

    def render_response(self, _filename, **context):
        return self.mako.render_response(self, _filename, **context)
