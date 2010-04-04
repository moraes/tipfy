# -*- coding: utf-8 -*-
"""
    tipfy.ext.db
    ~~~~~~~~~~~~~~~

    Model utilities extension.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import hashlib
import logging
import pickle
import re
import time
import unicodedata

from google.appengine.ext import db
from google.appengine.datastore import entity_pb
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError

from django.utils import simplejson

from pytz.gae import pytz

from tipfy import NotFound


def get_protobuf_from_entity(entities):
    """Converts one or more ``db.Model`` instances to encoded Protocol Buffers.

    This is useful to store entities in memcache, and preferable than storing
    the entities directly as it has slightly better performance and avoids
    crashes when unpickling (when, for example, the entity class is moved to a
    different module).

    Cached protobufs can be de-serialized using :func:`get_entity_from_protobuf`.

    Example usage:

    .. code-block:: python

       from google.appengine.api import memcache
       from tipfy.ext.db import get_protobuf_from_entity

       # Inside a handler, given that a MyModel model is defined.
       entity = MyModel(key_name='foo')
       entity.put()

       # Cache the protobuf.
       memcache.set('my-cache-key', get_protobuf_from_entity(entity))

    This function derives from `Nick's Blog`_.

    :param entities:
        A single or a list of ``db.Model`` instances to be serialized.
    :return:
        One or more entities serialized to Protocol Buffer (a string or a list).
    """
    if not entities:
        return None
    elif isinstance(entities, db.Model):
        return db.model_to_protobuf(entities).Encode()
    elif isinstance(entities, dict):
        return dict((k, db.model_to_protobuf(v).Encode()) for k, v in \
        entities.iteritems())
    else:
        return [db.model_to_protobuf(x).Encode() for x in entities]


def get_entity_from_protobuf(data):
    """Converts one or more encoded Protocol Buffers to ``db.Model`` instances.

    This is used to de-serialize entities previously serialized using
    :func:`get_protobuf_from_entity()`. After retrieving an entity protobuf
    from memcache, this converts it back to a ``db.Model`` instance.

    Example usage:

    .. code-block:: python

       from google.appengine.api import memcache
       from tipfy.ext.db import get_entity_from_protobuf

       # Get the protobuf from cache and de-serialize it.
       protobuf = memcache.get('my-cache-key')
       if protobuf:
           entity = get_entity_from_protobuf(protobuf)

    This function derives from `Nick's Blog`_.

    :param data:
        One or more entities serialized to Protocol Buffer (a string or a list).
    :return:
        One or more entities de-serialized from Protocol Buffers (a ``db.Model``
        inatance or a list of ``db.Model`` instances).
    """
    if not data:
        return None
    elif isinstance(data, str):
        return db.model_from_protobuf(entity_pb.EntityProto(data))
    elif isinstance(data, dict):
        return dict((k, db.model_from_protobuf(entity_pb.EntityProto(v))) for k, v \
        in data.iteritems())
    else:
        return [db.model_from_protobuf(entity_pb.EntityProto(x)) for x in data]


def get_reference_key(entity, prop_name):
    """Returns a encoded key from a ``db.ReferenceProperty`` without fetching
    the referenced entity.

    Example usage:

    .. code-block:: python

       from google.appengine.ext import db
       from tipfy.ext.db import get_reference_key

       # Set a book entity with an author reference.
       class Author(db.Model):
           name = db.StringProperty()

       class Book(db.Model):
           title = db.StringProperty()
           author = db.ReferenceProperty(Author)

       author = Author(name='Stephen King')
       author.put()

       book = Book(key_name='the-shining', title='The Shining', author=author)
       book.put()

       # Now let's fetch the book and get the author key without fetching it.
       fetched_book = Book.get_by_key_name('the-shining')
       assert str(author.key()) == str(get_reference_key(fetched_book,
           'author'))

    :param entity:
        A ``db.Model`` instance.
    :param prop_name:
        The name of the ``db.ReferenceProperty`` property.
    :return:
        An entity Key, as a string.
    """
    return getattr(entity.__class__, prop_name).get_value_for_datastore(entity)


def populate_entity(entity, **kwargs):
    """Sets a batch of property values in an entity. This is useful to set
    multiple properties coming from a form or set in a dictionary.

    Example usage:

    .. code-block:: python

       from google.appengine.ext import db
       from tipfy.ext.db import populate_entity

       class Author(db.Model):
           name = db.StringProperty(required=True)
           city = db.StringProperty()
           state = db.StringProperty()
           country = db.StringProperty()

       # Save an author entity.
       author = Author(key_name='stephen-king', name='Stephen King')
       author.put()

       # Now let's update the record.
       author = Author.get_by_key_name('stephen-king')
       populate_entity(author, city='Lovell', state='Maine', country='USA')
       author.put()

    :param entity:
        A ``db.Model`` instance.
    :param kwargs:
        Keyword arguments for each entity property value.
    :return:
        ``None``
    """
    properties = entity.properties().keys() + entity.dynamic_properties()
    for key, value in kwargs.iteritems():
        if key in properties:
            setattr(entity, key, value)


def get_property_dict(entity):
    """Returns a dictionary with all the properties and values in an entity.

    :param entity:
        A ``db.Model`` instance.
    :return:
        A dictionary mapping property names to values.
    """
    properties = entity.properties().keys() + entity.dynamic_properties()
    return dict((k, getattr(entity, k)) for k in properties)


def get_or_insert_with_flag(model, key_name, **kwargs):
    """Transactionally retrieve or create an instance of ``db.Model`` class.

    This is the same as ``db.Model.get_or_insert()``, but it returns a tuple
    ``(entity, flag)`` to indicate if the entity was inserted. If the entity
    is inserted, the flag is ``True``, otherwise it is ``False``.

    Example usage:

    .. code-block:: python

       from google.appengine.ext import db
       from tipfy.ext.db import get_or_insert_with_flag

       class Author(db.Model):
           name = db.StringProperty()

       author, is_new = get_or_insert_with_flag(Author, 'stephen-king',
           name='Stephen King')

    :param model:
        A ``db.Model`` class to fetch or create an entity.
    :param key_name:
        The entity's key name.
    :param kwargs:
        Keyword argumens to create an entity, if it doesn't exist yet.
    :return:
        A tuple ``(entity, flag)``, where entity is the fetched or inserted
        entity and flag is a boolean ``True`` if the entity was inserted or
        ``False`` if it existed already.
    """
    def txn():
        entity = model.get_by_key_name(key_name, parent=kwargs.get('parent'))
        if entity:
            return (entity, False)

        entity = model(key_name=key_name, **kwargs)
        entity.put()
        return (entity, True)

    return db.run_in_transaction(txn)


def get_or_404(model, key):
    """Returns a model instance fetched by key or raises a 404 Not Found error.

    Example usage:

    .. code-block:: python

        from tipfy import RequestHandler
        from tipfy.ext.db import retry_on_timeout
        from mymodels import Contact

        class EditContactHandler(RequestHandler):
            def get(self, **kwargs):
                contact = get_or_404(Contact, kwargs['contact_key'])

                # ... continue processing contact ...

    This function derives from `Kay`_.

    :param model:
        A ``db.Model`` class to load an entity.
    :param key:
        An encoded ``db.Key`` (a string).
    :return:
        A ``db.Model`` instance.
    """
    obj = model.get(key)
    if obj:
        return obj

    raise NotFound()


def get_by_id_or_404(model, id):
    """Returns a model instance fetched by id or raises a 404 Not Found error.


    Example usage:

    .. code-block:: python

        from tipfy import RequestHandler
        from tipfy.ext.db import get_by_id_or_404
        from mymodels import Contact

        class EditContactHandler(RequestHandler):
            def get(self, **kwargs):
                contact = get_by_id_or_404(Contact, kwargs['contact_id'])

                # ... continue processing contact ...

    This function derives from `Kay`_.

    :param model:
        A ``db.Model`` class to load an entity.
    :param id:
        An id from a ``db.Key`` (an integer).
    :return:
        A ``db.Model`` instance.
    """
    obj = model.get_by_id(id)
    if obj:
        return obj

    raise NotFound()


def get_by_key_name_or_404(model, key_name):
    """Returns a model instance fetched by key name or raises a 404 Not Found
    error.


    Example usage:

    .. code-block:: python

        from tipfy import RequestHandler
        from tipfy.ext.db import get_by_key_name_or_404
        from mymodels import Contact

        class EditContactHandler(RequestHandler):
            def get(self, **kwargs):
                contact = get_by_key_name_or_404(Contact,
                    kwargs['contact_key_name'])

                # ... continue processing contact ...

    This function derives from `Kay`_.

    :param model:
        A ``db.Model`` class to load an entity.
    :param key_name:
        A key name from a ``db.Key`` (a string).
    :return:
        A ``db.Model`` instance.
    """
    obj = model.get_by_key_name(key_name)
    if obj:
        return obj

    raise NotFound()


# Decorators.
def retry_on_timeout(retries=3, interval=1.0, exponent=2.0):
    """A decorator to retry a function that performs db operations in case a
    ``db.Timeout`` exception is raised.

    Example usage:

    .. code-block:: python

        from tipfy import RequestHandler
        from tipfy.ext.db import retry_on_timeout
        from mymodels import Contact

        class EditContactHandler(RequestHandler):
            def get(self, **kwargs):
                # ... do the get stuff ...
                # ...
                pass

            @retry_on_timeout()
            def post(self, **kwargs):
                # ... load entity and process form data ...
                # ...

                # Save the entity. This will be retried in case of timeouts.
                entity.put()

    This function derives from `Kay`_.

    :param retries:
        An integer value for the number of retries in case ``db.Timeout`` is
        raised.
    :param interval:
        A float value for the number of seconds between each interval.
    :param exponent:
        A float exponent to be applied to each retry interval. For example, if
        `interval` is set to `0.2` and exponent is `2.0`, retries intervals
        will be in seconds: `0.2`, `0.4`, `0.8`, etc.
    :return:
        A decorator wrapping the target function.
    """
    def decorator(func):
        def decorated(*args, **kwargs):
            count = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except db.Timeout, e:
                    logging.debug(e)
                    if count >= retries:
                        raise e
                    else:
                        sleep_time = (exponent ** count) * interval
                        logging.warning("Retrying function %r in %d secs" %
                            (func, sleep_time))
                        time.sleep(sleep_time)
                        count += 1

        return decorated

    return decorator


def load_entity(model, kwarg_old, kwarg_new=None, fetch_mode=None):
    """A decorator that takes an entity key, key name or id from the request
    handler keyword arguments, load an entity and add it to the arguments.
    If not found, a ``NotFound`` error is raised.

    Example usage:

    .. code-block:: python

        from tipfy import RequestHandler
        from tipfy.ext.db import load_entity
        from mymodels import Contact

        class EditContactHandler(RequestHandler):
            @load_entity(Contact, 'contact_id', 'contact', 'id')
            def get(self, **kwargs):
                # kwargs['contact_id'] is used to load a Contact entity using
                # get_by_id(). The entity is then added to kwargs['contact'].
                pass

            @load_entity(Contact, 'contact_id', 'contact', 'id')
            def post(self, **kwargs):
                # kwargs['contact_id'] is used to load a Contact entity using
                # get_by_id(). The entity is then added to kwargs['contact'].
                pass

    :param model:
        A ``db.Model`` class to fetch an entity from.
    :param kwarg_old:
        The keyword argument, passed by the routing system to the request
        handler, that contains the key, id or key_name of the entity to be
        loaded. For example, `contact_key`, `contact_id` or `contact_key_name`.
    :param kwarg_new:
        The new keyword argument to be passed to the request handler. This
        keyword is **added** to the arguments. If not set, uses kwarg_old as
        base, removing the fetch mode sufix. For example, `contact`.
    :param fetch_mode:
        The fetch mode. Can be either `key`, `id` or `key_name`, to fetch using
        ``db.Model.get()``, ``db.Model.get_by_id()`` or
        ``db.Model.get_by_key_name()``, respectively. If not set, it will check
        if `kwargs_old` ends with `_key`, `_id` or `_key_name` to guess the
        fetch mode.
    :return:
        A decorator wrapping the target ``tipfy.RequestHandler`` method.
    """
    if fetch_mode is None or kwarg_new is None:
        for sufix in ('_key', '_id', '_key_name'):
            if kwarg_old.endswith(sufix):
                if kwarg_new is None:
                    kwarg_new = kwarg_old[:-len(sufix)]

                if fetch_mode is None:
                    fetch_mode = sufix[1:]

                break

    if fetch_mode == 'key':
        fetcher = get_or_404
    elif fetch_mode == 'id':
        fetcher = get_by_id_or_404
    elif fetch_mode == 'key_name':
        fetcher = get_by_key_name_or_404
    else:
        raise NotImplementedError('Invalid fetch_mode.')

    def decorator(func):
        def decorated(*args, **kwargs):
            entity = None
            key = kwargs.get(kwarg_old, None)
            if key is not None:
                entity = fetcher(model, key)

            kwargs[kwarg_new] = entity
            return func(*args, **kwargs)

        return decorated

    return decorator


# Extra db.Model property classes.
class EtagProperty(db.Property):
    """Automatically creates an ETag based on the value of another property.

    Note: the ETag is only set or updated after the entity is saved.

    Example usage:

    .. code-block:: python

       from google.appengine.ext import db
       from tipfy.ext.db import EtagProperty

       class StaticContent(db.Model):
           data = db.BlobProperty()
           etag = EtagProperty(data)

    This class derives from `aetycoon`_.
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


class JsonProperty(db.Property):
    """Stores a value automatically encoding to JSON on set and decoding
    on get.

    Example usage:

    >>> class JsonModel(db.Model):
    ... data = JsonProperty()
    >>> model = PickleModel()
    >>> model.data = {"foo": "bar"}
    >>> model.data
    {'foo': 'bar'}
    >>> model.put() # doctest: +ELLIPSIS
    datastore_types.Key.from_path(u'PickleModel', ...)
    >>> model2 = PickleModel.all().get()
    >>> model2.data
    {'foo': 'bar'}
    """
    data_type = db.Text

    def get_value_for_datastore(self, model_instance):
        """Encodes the value to JSON."""
        value = super(JsonProperty, self).get_value_for_datastore(
            model_instance)
        if value is not None:
            return db.Text(simplejson.dumps(value))

    def make_value_from_datastore(self, value):
        """Decodes the value from JSON."""
        if value is not None:
            return simplejson.loads(value)

    def validate(self, value):
        if value is not None and not isinstance(value, (dict, list, tuple)):
            raise db.BadValueError('Property %s must be a dict, list or '
                'tuple.' % self.name)

        return value


class PickleProperty(db.Property):
    """A property for storing complex objects in the datastore in pickled form.

    Example usage:

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

    This class derives from `aetycoon`_.
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

    Note: the slug is only set or updated after the entity is saved.

    Example usage:

    .. code-block:: python

       from google.appengine.ext import db
       from tipfy.ext.db import SlugProperty

       class BlogPost(db.Model):
           title = db.StringProperty()
           slug = SlugProperty(title)

    This class derives from `aetycoon`_.
    """
    def __init__(self, prop, max_length=None, *args, **kwargs):
        self.prop = prop
        self.max_length = max_length
        super(SlugProperty, self).__init__(*args, **kwargs)

    def get_value_for_datastore(self, model_instance):
        v = self.prop.__get__(model_instance, type(model_instance))
        if not v:
            return self.default

        return _slugify(v, max_length=self.max_length, default=self.default)


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


def _slugify(value, max_length=None, default=None):
    """Converts a string to slug format (all lowercase, words separated by
    dashes).

    :param value:
        The string to be slugified.
    :param max_length:
        An intebger to restrict the resulting string to this maximum length.
        Words are not broken when restricting length.
    :param default:
        A default value in case the resulting string is empty.
    :return:
        A slugified string.
    """
    if not isinstance(value, unicode):
        value = value.decode('utf8')

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
