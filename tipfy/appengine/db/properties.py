# -*- coding: utf-8 -*-
"""
    tipfy.appengine.db.properties
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Extra db.Model property classes.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import hashlib
import pickle

from google.appengine.ext import db

from tipfy.utils import json_decode, json_encode, slugify

try:
    # This is optional, only required by TimezoneProperty.
    from pytz.gae import pytz
except ImportError, e:
    pass


class EtagProperty(db.Property):
    """Automatically creates an ETag based on the value of another property.

    Note: the ETag is only set or updated after the entity is saved.
    Example::

        from google.appengine.ext import db
        from tipfy.appengine.db import EtagProperty

        class StaticContent(db.Model):
            data = db.BlobProperty()
            etag = EtagProperty(data)

    This class derives from `aetycoon <http://github.com/Arachnid/aetycoon>`_.
    """
    def __init__(self, prop, *args, **kwargs):
        self.prop = prop
        super(EtagProperty, self).__init__(*args, **kwargs)

    def get_value_for_datastore(self, model_instance):
        v = self.prop.__get__(model_instance, type(model_instance))
        if not v:
            return None

        if isinstance(v, unicode):
            v = v.encode('utf-8')

        return hashlib.sha1(v).hexdigest()


class KeyProperty(db.Property):
    """A property that stores a key, without automatically dereferencing it.

    Example usage:

    >>> class SampleModel(db.Model):
    ...   sample_key = KeyProperty()

    >>> model = SampleModel()
    >>> model.sample_key = db.Key.from_path("Foo", "bar")
    >>> model.put() # doctest: +ELLIPSIS
    datastore_types.Key.from_path(u'SampleModel', ...)

    >>> model.sample_key # doctest: +ELLIPSIS
    datastore_types.Key.from_path(u'Foo', u'bar', ...)

    Adapted from aetycoon: http://github.com/Arachnid/aetycoon/
    Added possibility to set it using a db.Model instance.
    """
    def validate(self, value):
        """Validate the value.

        Args:
          value: The value to validate.
        Returns:
          A valid key.
        """
        if isinstance(value, basestring):
            value = db.Key(value)
        elif isinstance(value, db.Model):
            if not value.has_key():
                raise db.BadValueError('%s instance must have a complete key to '
                    'be stored.' % value.__class__.kind())

            value = value.key()

        if value is not None:
            if not isinstance(value, db.Key):
                raise TypeError('Property %s must be an instance of db.Key'
                    % self.name)

        return super(KeyProperty, self).validate(value)


class JsonProperty(db.Property):
    """Stores a value automatically encoding to JSON on set and decoding
    on get.
    """
    data_type = db.Text

    def get_value_for_datastore(self, model_instance):
        """Encodes the value to JSON."""
        value = super(JsonProperty, self).get_value_for_datastore(
            model_instance)
        if value is not None:
            return db.Text(json_encode(value, separators=(',', ':')))

    def make_value_from_datastore(self, value):
        """Decodes the value from JSON."""
        if value is not None:
            return json_decode(value)

    def validate(self, value):
        if value is not None and not isinstance(value, (dict, list, tuple)):
            raise db.BadValueError('Property %s must be a dict, list or '
                'tuple.' % self.name)

        return value


class PickleProperty(db.Property):
    """A property for storing complex objects in the datastore in pickled form.
    Example::

        >>> class PickleModel(db.Model):
        ... data = PickleProperty()
        >>> model = PickleModel()
        >>> model.data = {"foo": "bar"}
        >>> model.data
        {'foo': 'bar'}
        >>> model.put() # doctest: +ELLIPSIS
        datastore_types.Key.from_path(u'PickleModel', ...)
        >>> model2 = PickleModel.all().get()
        >>> model2.data
        {'foo': 'bar'}

    This class derives from `aetycoon <http://github.com/Arachnid/aetycoon>`_.
    """
    data_type = db.Blob

    def get_value_for_datastore(self, model_instance):
        value = self.__get__(model_instance, model_instance.__class__)
        value = self.validate(value)

        if value is not None:
            return db.Blob(pickle.dumps(value, pickle.HIGHEST_PROTOCOL))

    def make_value_from_datastore(self, value):
        if value is not None:
            return pickle.loads(str(value))


class SlugProperty(db.Property):
    """Automatically creates a slug (a lowercase string with words separated by
    dashes) based on the value of another property.

    Note: the slug is only set or updated after the entity is saved. Example::

        from google.appengine.ext import db
        from tipfy.appengine.db import SlugProperty

        class BlogPost(db.Model):
            title = db.StringProperty()
            slug = SlugProperty(title)

    This class derives from `aetycoon <http://github.com/Arachnid/aetycoon>`_.
    """
    def __init__(self, prop, max_length=None, *args, **kwargs):
        self.prop = prop
        self.max_length = max_length
        super(SlugProperty, self).__init__(*args, **kwargs)

    def get_value_for_datastore(self, model_instance):
        v = self.prop.__get__(model_instance, type(model_instance))
        if not v:
            return self.default

        return slugify(v, max_length=self.max_length, default=self.default)


class TimezoneProperty(db.Property):
    """Stores a timezone value."""
    data_type = str

    def get_value_for_datastore(self, model_instance):
        value = super(TimezoneProperty, self).get_value_for_datastore(
            model_instance)
        value = self.validate(value)
        return value.zone

    def make_value_from_datastore(self, value):
        return pytz.timezone(value)

    def validate(self, value):
        value = super(TimezoneProperty, self).validate(value)
        if value is None or hasattr(value, 'zone'):
            return value
        elif isinstance(value, basestring):
            return pytz.timezone(value)

        raise db.BadValueError("Property %s must be a pytz timezone or string."
            % self.name)
