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

from tipfy import local, get_config

#: Default configuration values for this module. Keys are:
#:   - ``templates_dir``: Directory for templates. Default is `templates`.
default_config = {
    'templates_dir': 'templates',
}

# TemplateLookup cached in the module.
_lookup = None


def get_lookup():
    global _lookup
    if _lookup is None:
        _lookup = TemplateLookup(directories=[path.join(get_config(__name__,
            'templates_dir'))], output_encoding='utf-8',
            encoding_errors='replace')

    return _lookup


def render_template(filename, **context):
    """Renders a template."""
    template = get_lookup().get_template(filename)
    buf = StringIO()
    template.render_context(Context(buf, **context))
    return buf.getvalue()


def render_response(filename, **context):
    """Renders a template and returns a response object."""
    local.response.data = render_template(filename, **context)
    local.response.mimetype = 'text/html'
    return local.response
