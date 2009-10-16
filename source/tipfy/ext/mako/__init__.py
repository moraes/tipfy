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
from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO

from tipfy import local


def render_template(filename, **context):
    """Renders a template."""
    template = Template(filename=path.join('templates', filename))
    buf = StringIO()
    template.render_context(Context(buf, **context))
    return buf.getvalue()


def render_response(filename, **context):
    """Renders a template and returns a response object."""
    local.response.data = render_template(filename, **context)
    local.response.mimetype = 'text/html'
    return local.response
