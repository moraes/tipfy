# -*- coding: utf-8 -*-
"""
    tipfy.ext.mako
    ~~~~~~~~~~~~~~

    Mako template engine extension.

    It requires the mako module to be added to the lib dir. Mako can be
    downloaded at http://www.makotemplates.org/

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from os import path
from mako.lookup import TemplateLookup
from mako.runtime import Context
from StringIO import StringIO

from tipfy import local, app, response

lookup = TemplateLookup(directories=[path.join(app.config.templates_dir)],
    output_encoding='utf-8', encoding_errors='replace')


def render_template(filename, **context):
    """Renders a template."""
    template = lookup.get_template(filename)
    buf = StringIO()
    template.render_context(Context(buf, **context))
    return buf.getvalue()


def render_response(filename, **context):
    """Renders a template and returns a response object."""
    response.data = render_template(filename, **context)
    response.mimetype = 'text/html'
    return response
