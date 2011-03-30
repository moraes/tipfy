# -*- coding: utf-8 -*-
"""
    tipfy.json
    ~~~~~~~~~~

    JSON encoder/decoder.

    :copyright: 2011 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from __future__ import absolute_import

import base64

try:
    # Preference for installed library with updated fixes.
    import simplejson as json
except ImportError:
    try:
        # Standard library module in Python 2.6.
        import json
    except (ImportError, AssertionError):
        try:
            # Google App Engine.
            from django.utils import simplejson as json
        except ImportError:
            raise RuntimeError(
                'A JSON parser is required, e.g., simplejson at '
                'http://pypi.python.org/pypi/simplejson/')

assert hasattr(json, 'loads') and hasattr(json, 'dumps')


def json_encode(value, *args, **kwargs):
    """Serializes a value to JSON.

    :param value:
        A value to be serialized.
    :param args:
        Extra arguments to be passed to `json.dumps()`.
    :param kwargs:
        Extra keyword arguments to be passed to `json.dumps()`.
    :returns:
        The serialized value.
    """
    # JSON permits but does not require forward slashes to be escaped.
    # This is useful when json data is emitted in a <script> tag
    # in HTML, as it prevents </script> tags from prematurely terminating
    # the javscript.  Some json libraries do this escaping by default,
    # although python's standard library does not, so we do it here.
    # http://stackoverflow.com/questions/1580647/json-why-are-forward-slashes-escaped
    kwargs.setdefault('separators', (',', ':'))
    return json.dumps(value, *args, **kwargs).replace("</", "<\\/")


def json_decode(value, *args, **kwargs):
    """Deserializes a value from JSON.

    :param value:
        A value to be deserialized.
    :param args:
        Extra arguments to be passed to `json.loads()`.
    :param kwargs:
        Extra keyword arguments to be passed to `json.loads()`.
    :returns:
        The deserialized value.
    """
    if isinstance(value, str):
        value = value.decode('utf-8')

    assert isinstance(value, unicode)
    return json.loads(value, *args, **kwargs)


def json_b64encode(value):
    """Serializes a value to JSON and encodes it to base64.

    :param value:
        A value to be encoded.
    :returns:
        The encoded value.
    """
    return base64.b64encode(json_encode(value))


def json_b64decode(value):
    """Decodes a value from base64 and deserializes it from JSON.

    :param value:
        A value to be decoded.
    :returns:
        The decoded value.
    """
    return json_decode(base64.b64decode(value))
