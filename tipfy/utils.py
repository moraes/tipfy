#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Escaping/unescaping methods for HTML, JSON, URLs, and others."""
import base64
import htmlentitydefs
import re
import unicodedata
import urllib
import xml.sax.saxutils

from .app import current_handler

try:
    # Preference for installed library with updated fixes.
    import simplejson
except ImportError:
    try:
        # Standard library module in Python 2.6.
        import json as simplejson
        assert hasattr(simplejson, 'loads') and hasattr(simplejson, 'dumps')
    except (ImportError, AssertionError):
        try:
            # Google App Engine.
            from django.utils import simplejson
        except ImportError:
            raise RuntimeError('A JSON parser is required, e.g., '
                'simplejson at http://pypi.python.org/pypi/simplejson/')


def xhtml_escape(value):
    """Escapes a string so it is valid within XML or XHTML.

    :param value:
        The value to be escaped.
    :returns:
        The escaped value.
    """
    return utf8(xml.sax.saxutils.escape(value, {'"': "&quot;"}))


def xhtml_unescape(value):
    """Un-escapes an XML-escaped string.

    :param value:
        The value to be un-escaped.
    :returns:
        The un-escaped value.
    """
    return re.sub(r"&(#?)(\w+?);", _convert_entity, _unicode(value))


def json_encode(value, *args, **kwargs):
    """Serializes a value to JSON.

    :param value:
        A value to be serialized.
    :param args:
        Extra arguments to be passed to `simplejson.dumps()`.
    :param kwargs:
        Extra keyword arguments to be passed to `simplejson.dumps()`.
    :returns:
        The serialized value.
    """
    # JSON permits but does not require forward slashes to be escaped.
    # This is useful when json data is emitted in a <script> tag
    # in HTML, as it prevents </script> tags from prematurely terminating
    # the javscript.  Some json libraries do this escaping by default,
    # although python's standard library does not, so we do it here.
    # http://stackoverflow.com/questions/1580647/json-why-are-forward-slashes-escaped
    return simplejson.dumps(value, *args, **kwargs).replace("</", "<\\/")


def json_decode(value, *args, **kwargs):
    """Deserializes a value from JSON.

    :param value:
        A value to be deserialized.
    :param args:
        Extra arguments to be passed to `simplejson.loads()`.
    :param kwargs:
        Extra keyword arguments to be passed to `simplejson.loads()`.
    :returns:
        The deserialized value.
    """
    return simplejson.loads(_unicode(value), *args, **kwargs)


def json_b64encode(value):
    """Serializes a value to JSON and encodes it to base64.

    :param value:
        A value to be encoded.
    :returns:
        The encoded value.
    """
    return base64.b64encode(json_encode(value, separators=(',', ':')))


def json_b64decode(value):
    """Decodes a value from base64 and deserializes it from JSON.

    :param value:
        A value to be decoded.
    :returns:
        The decoded value.
    """
    return json_decode(base64.b64decode(value))


def render_json_response(*args, **kwargs):
    """Renders a JSON response.

    :param args:
        Arguments to be passed to json_encode().
    :param kwargs:
        Keyword arguments to be passed to json_encode().
    :returns:
        A :class:`Response` object with a JSON string in the body and
        mimetype set to ``application/json``.
    """
    return current_handler.app.response_class(json_encode(*args, **kwargs),
        mimetype='application/json')


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
    """Encodes a unicode value to UTF-8 if not yet encoded.

    :param value:
        Value to be encoded.
    :returns:
        An encoded string.
    """
    if isinstance(value, unicode):
        return value.encode("utf-8")

    assert isinstance(value, str)
    return value


def _unicode(value):
    """Encodes a string value to unicode if not yet decoded.

    :param value:
        Value to be decoded.
    :returns:
        A decoded string.
    """
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
    return dict((name, unichr(value)) for \
        name, value in htmlentitydefs.name2codepoint.iteritems())


def url_for(_name, **kwargs):
    """A proxy to :meth:`RequestHandler.url_for`.

    .. seealso:: :meth:`Router.build`.
    """
    return current_handler.url_for(_name, **kwargs)


def slugify(value, max_length=None, default=None):
    """Converts a string to slug format (all lowercase, words separated by
    dashes).

    :param value:
        The string to be slugified.
    :param max_length:
        An integer to restrict the resulting string to a maximum length.
        Words are not broken when restricting length.
    :param default:
        A default value in case the resulting string is empty.
    :returns:
        A slugified string.
    """
    value = _unicode(value)
    s = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').lower()
    s = re.sub('-+', '-', re.sub('[^a-zA-Z0-9-]+', '-', s)).strip('-')
    if not s:
        return default

    if max_length:
        # Restrict length without breaking words.
        while len(s) > max_length:
            if s.find('-') == -1:
                s = s[:max_length]
            else:
                s = s.rsplit('-', 1)[0]

    return s


_HTML_UNICODE_MAP = _build_unicode_map()
