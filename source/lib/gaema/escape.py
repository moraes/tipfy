# -*- coding: utf-8 -*-
"""
    gaema.escape
    ~~~~~~~~~~~~

    Escaping/unescaping methods for HTML, JSON, URLs, and others.

    :copyright: 2009 by Facebook.
    :license: Apache License Version 2.0. See LICENSE.txt for more details.
"""
import htmlentitydefs
import re
import xml.sax.saxutils
import urllib

from django.utils import simplejson


def xhtml_escape(value):
    """Escapes a string so it is valid within XML or XHTML."""
    return utf8(xml.sax.saxutils.escape(value))


def xhtml_unescape(value):
    """Un-escapes an XML-escaped string."""
    return re.sub(r"&(#?)(\w+?);", _convert_entity, _unicode(value))


def json_encode(value):
    """JSON-encodes the given Python object."""
    return simplejson.dumps(value)


def json_decode(value):
    """Returns Python objects for the given JSON string."""
    return simplejson.loads(_unicode(value))


def squeeze(value):
    """Replace all sequences of whitespace chars with a single space."""
    return re.sub(r"[\x00-\x20]+", " ", value).strip()


def url_escape(value):
    """Returns a valid URL-encoded version of the given value."""
    return urllib.quote_plus(utf8(value))


def url_unescape(value):
    """Decodes the given value from a URL."""
    return _unicode(urllib.unquote_plus(value))


def utf8(value):
    if isinstance(value, unicode):
        return value.encode("utf-8")
    assert isinstance(value, str)
    return value


def _unicode(value):
    if isinstance(value, str):
        return value.decode("utf-8")
    assert isinstance(value, unicode)
    return value


def _convert_entity(m):
    if m.group(1) == "#":
        try:
            return unichr(int(m.group(2)))
        except ValueError:
            return "&#%s;" % m.group(2)
    try:
        return _HTML_UNICODE_MAP[m.group(2)]
    except KeyError:
        return "&%s;" % m.group(2)


def _build_unicode_map():
    unicode_map = {}
    for name, value in htmlentitydefs.name2codepoint.iteritems():
        unicode_map[name] = unichr(value)
    return unicode_map

_HTML_UNICODE_MAP = _build_unicode_map()
