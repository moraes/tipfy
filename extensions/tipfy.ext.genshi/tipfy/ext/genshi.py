# -*- coding: utf-8 -*-
"""
    tipfy.ext.genshi
    ~~~~~~~~~~~~~~~~

    Genshi template support for Tipfy.

    :copyright: (c) 2010 by Dag Odenhall <dag.odenhall@gmail.com>.
    :copyright: (c) 2010 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from collections import defaultdict
from os.path import splitext

from genshi.template import NewTextTemplate, TemplateLoader

from werkzeug import cached_property

from tipfy import Tipfy

#: Default configuration values for this module. Keys are:
#:
#: - ``templates_dir``: Directory for templates. Default is `templates`.
default_config = {
    'templates_dir': 'templates',
}


class GenshiMixin(object):
    """:class:`tipfy.RequestHandler` mixing to add a convenient
    ``render_response`` function to handlers. It expects a ``context``
    dictionary to be set in the handler, so that the passed values are added to
    the context. The idea is that other mixins can use this context to set
    template values.
    """
    def render_template(self, filename, _method=None, **context):
        """Renders a template and returns a response object. It will pass

        :param filename:
            The template filename, related to the templates directory.
        :param _method:
            The render method: 'html', 'xml', 'css', 'js' or 'txt'.
        :param context:
            Keyword arguments used as variables in the rendered template.
            These will override values set in the request context.
       :return:
            A :class:`tipfy.Response` object with the rendered template.
        """
        request_context = dict(self.request.context)
        request_context.update(context)
        return render_template(filename, _method=method, **request_context)

    def render_response(self, filename, _method=None, **context):
        """Returns a response object with a rendered template. It will pass

        :param filename:
            The template filename, related to the templates directory.
        :param _method:
            The render method: 'html', 'xml', 'css', 'js' or 'txt'.
        :param context:
            Keyword arguments used as variables in the rendered template.
            These will override values set in the request context.
        :return:
            A :class:`tipfy.Response` object with the rendered template.
        """
        request_context = dict(self.request.context)
        request_context.update(context)
        return render_response(filename, _method=method, **request_context)


class Genshi(object):
    def __init__(self, app):
        self.app = app

        #: What method is used for an extension.
        self.extensions = {
            'html': 'html',
            'xml': 'xml',
            'txt': 'text',
            'js': 'js',
            'css': 'css'
        }

        #: Render methods.
        self.methods = {
            'html': {
                'serializer': 'html',
                'doctype': 'html',
            },
            'html5': {
                'serializer': 'html',
                'doctype': 'html5',
            },
            'xhtml': {
                'serializer': 'xhtml',
                'doctype': 'xhtml',
                'mimetype': 'application/xhtml+xml'
            },
            'xml': {
                'serializer': 'xml',
                'mimetype': 'application/xml'
            },
            'text': {
                'serializer': 'text',
                'mimetype': 'text/plain',
                'class': NewTextTemplate
            },
            'js': {
                'serializer': 'text',
                'mimetype': 'application/javascript',
                'class': NewTextTemplate
            },
            'css': {
                'serializer': 'text',
                'mimetype': 'text/css',
                'class': NewTextTemplate
            }
        }

        #: Filter functions to be applied to templates.
        self.filters = defaultdict(list)

    @cached_property
    def template_loader(self):
        """A :class:`genshi.template.TemplateLoader` that loads templates
        from the same place as Flask.

        :return:
            A ``TemplateLoader`` instance.
        """
        return TemplateLoader(self.app.get_config(__name__, 'templates_dir'),
            auto_reload=self.app.dev)

    def select_method(self, filename, method=None):
        """Selects a method from :attr:`Genshi.methods`
        based on the file extension of ``template``
        and :attr:`Genshi.extensions`, or based on ``method``.

        :param filename:
            The template filename, related to the templates directory.
        :param _method:
            The render method: 'html', 'xml', 'css', 'js' or 'txt'.
        :return:
            A rendering method name.
        """
        if method is None:
            ext = splitext(filename)[1][1:]
            return self.extensions[ext]

        return method


def get_genshi_instance():
    """Returns an instance of :class:`Genshi`, registering it in the WSGI app
    if not yet registered.

    :return:
        An instance of :class:`Genshi`.
    """
    registry = Tipfy.app.registry
    if 'genshi_instance' not in registry:
        registry['genshi_instance'] = Genshi(Tipfy.app)

    return registry['genshi_instance']


def generate_template(filename, _method=None, **context):
    """Creates a Genshi filename stream that you can
    run filters and transformations on.

    :param filename:
        The template filename, related to the templates directory.
    :param _method:
        The render method: 'html', 'xml', 'css', 'js' or 'txt'.
    :param context:
        Keyword arguments used as variables in the rendered template.
    :return:
        A Genshi template stream.
    """
    genshi = get_genshi_instance()
    method = genshi.select_method(filename, _method)
    class_ = genshi.methods[method].get('class')
    template = genshi.template_loader.load(filename, cls=class_)
    template = template.generate(**context)

    for filter in genshi.filters[method]:
        template = filter(template)

    return template


def render_template(filename, _method=None, **context):
    """Renders a template to a string.

    :param filename:
        The template filename, related to the templates directory.
    :param _method:
        The render method: 'html', 'xml', 'css', 'js' or 'txt'.
    :param context:
        Keyword arguments used as variables in the rendered template.
    :return:
        A rendered template.
    """
    genshi = get_genshi_instance()
    method = genshi.select_method(filename, _method)
    template = generate_template(filename, method, **context)
    render_args = dict(method=genshi.methods[method]['serializer'])

    if 'doctype' in genshi.methods[method]:
        render_args['doctype'] = genshi.methods[method]['doctype']

    return template.render(**render_args)


def render_response(filename, _method=None, **context):
    """Renders a template and wraps it in a :attr:`~flask.Flask.response_class`
    with mimetype set according to the rendering method.

    :param filename:
        The template filename, related to the templates directory.
    :param _method:
        The render method: 'html', 'xml', 'css', 'js' or 'txt'.
    :param context:
        Keyword arguments used as variables in the rendered template.
    :return:
        A :class:`tipfy.Response` instance with the rendered template.
    """
    genshi = get_genshi_instance()
    method = genshi.select_method(filename, _method)
    mimetype = genshi.methods[method].get('mimetype', 'text/html')
    template = render_template(filename, method, **context)
    return Tipfy.app.response_class(template, mimetype=mimetype)
