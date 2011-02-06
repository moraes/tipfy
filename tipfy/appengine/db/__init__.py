# -*- coding: utf-8 -*-
"""
    tipfy.appengine.db
    ~~~~~~~~~~~~~~~~~~

    Datastore utilities extension.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import logging
import time

from google.appengine.api import datastore_errors
from google.appengine.api.namespace_manager import namespace_manager
from google.appengine.ext import db

from werkzeug import abort


def get_protobuf_from_entity(entities):
    """Converts one or more ``db.Model`` instances to encoded Protocol Buffers.

    This is useful to store entities in memcache, and preferable than storing
    the entities directly as it has slightly better performance and avoids
    crashes when unpickling (when, for example, the entity class is moved to a
    different module).

    Cached protobufs can be de-serialized using
    :func:`get_entity_from_protobuf`. Example::

        from google.appengine.api import memcache
        from tipfy.appengine.db import get_protobuf_from_entity

        # Inside a handler, given that a MyModel model is defined.
        entity = MyModel(key_name='foo')
        entity.put()

        # Cache the protobuf.
        memcache.set('my-cache-key', get_protobuf_from_entity(entity))

    This function derives from `Nick's Blog <http://blog.notdot.net/2009/9/Efficient-model-memcaching>`_.

    :param entities:
        A single or a list of ``db.Model`` instances to be serialized.
    :returns:
        One or more entities serialized to Protocol Buffer (a string or a
        list).
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
    :func:`get_protobuf_from_entity`. After retrieving an entity protobuf
    from memcache, this converts it back to a ``db.Model`` instance.
    Example::

        from google.appengine.api import memcache
        from tipfy.appengine.db import get_entity_from_protobuf

        # Get the protobuf from cache and de-serialize it.
        protobuf = memcache.get('my-cache-key')
        if protobuf:
            entity = get_entity_from_protobuf(protobuf)

    This function derives from `Nick's Blog <http://blog.notdot.net/2009/9/Efficient-model-memcaching>`_.

    :param data:
        One or more entities serialized to Protocol Buffer (a string or a
        list).
    :returns:
        One or more entities de-serialized from Protocol Buffers (a
        ``db.Model`` inatance or a list of ``db.Model`` instances).
    """
    if not data:
        return None
    elif isinstance(data, str):
        return db.model_from_protobuf(data)
    elif isinstance(data, dict):
        return dict((k, db.model_from_protobuf(v)) for k, v in data.iteritems())
    else:
        return [db.model_from_protobuf(x) for x in data]


def get_reference_key(entity, prop_name):
    """Returns a encoded key from a ``db.ReferenceProperty`` without fetching
    the referenced entity. Example::

        from google.appengine.ext import db
        from tipfy.appengine.db import get_reference_key

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
    :returns:
        An entity Key, as a string.
    """
    return getattr(entity.__class__, prop_name).get_value_for_datastore(entity)


def populate_entity(entity, **kwargs):
    """Sets a batch of property values in an entity. This is useful to set
    multiple properties coming from a form or set in a dictionary. Example::

        from google.appengine.ext import db
        from tipfy.appengine.db import populate_entity

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
    :returns:
        None.
    """
    properties = get_entity_properties(entity)
    for key, value in kwargs.iteritems():
        if key in properties:
            setattr(entity, key, value)


def get_entity_properties(entity):
    """Returns a list with all property names in an entity.

    :param entity:
        A ``db.Model`` instance.
    :returns:
        A list with all property names in the entity.
    """
    return entity.properties().keys() + entity.dynamic_properties()


def get_entity_dict(entities):
    """Returns a dictionary with all the properties and values in an entity.

    :param entities:
        One or more ``db.Model`` instances.
    :returns:
        A dictionary or a list of dictionaries mapping property names to
        values.
    """
    if isinstance(entities, db.Model):
        return _get_entity_dict(entities)

    return [_get_entity_dict(e) for e in entities]


def _get_entity_dict(entity):
    """See :func:`get_entity_dict`."""
    return dict((k, getattr(entity, k)) for k in get_entity_properties(entity))


def get_or_insert_with_flag(model, key_name, **kwargs):
    """Transactionally retrieve or create an instance of ``db.Model`` class.

    This is the same as ``db.Model.get_or_insert()``, but it returns a tuple
    ``(entity, flag)`` to indicate if the entity was inserted. If the entity
    is inserted, the flag is True, otherwise it is False. Example::

        from google.appengine.ext import db
        from tipfy.appengine.db import get_or_insert_with_flag

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
    :returns:
        A tuple ``(entity, flag)``, where entity is the fetched or inserted
        entity and flag is a boolean True if the entity was inserted or
        False if it existed already.
    """
    def txn():
        entity = model.get_by_key_name(key_name, parent=kwargs.get('parent'))
        if entity:
            return (entity, False)

        entity = model(key_name=key_name, **kwargs)
        entity.put()
        return (entity, True)

    return db.run_in_transaction(txn)


def get_or_404(*args, **kwargs):
    """Returns a model instance fetched by key or raises a 404 Not Found error.
    Example:

        from tipfy import RequestHandler
        from tipfy.appengine.db import get_or_404
        from mymodels import Contact

        class EditContactHandler(RequestHandler):
            def get(self, **kwargs):
                contact = get_or_404(kwargs['contact_key'])

                # ... continue processing contact ...

    This function derives from `Kay <http://code.google.com/p/kay-framework/>`_.

    :param args:
        Positional arguments to construct a key using ``db.Key.from_path()``
        or a ``db.Key`` instance or encoded key.
    :param kwargs:
        Keyword arguments to construct a key using ``db.Key.from_path()``.
    :returns:
        A ``db.Model`` instance.
    """
    try:
        if len(args) == 1:
            # A Key or encoded Key is the single argument.
            obj = db.get(args[0])
        else:
            # Build a key using all arguments.
            obj = db.get(db.Key.from_path(*args, **kwargs))

        if obj:
            return obj
    except (db.BadArgumentError, db.BadKeyError):
        # Falling through to raise the NotFound.
        pass

    abort(404)


def get_by_id_or_404(model, id, parent=None):
    """Returns a model instance fetched by id or raises a 404 Not Found error.
    Example::

        from tipfy import RequestHandler
        from tipfy.appengine.db import get_by_id_or_404
        from mymodels import Contact

        class EditContactHandler(RequestHandler):
            def get(self, **kwargs):
                contact = get_by_id_or_404(Contact, kwargs['contact_id'])

                # ... continue processing contact ...

    This function derives from `Kay <http://code.google.com/p/kay-framework/>`_.

    :param model:
        A ``db.Model`` class to load an entity.
    :param id:
        An id from a ``db.Key`` (an integer).
    :param parent:
        The parent entity for the requested entities, as a Model
        instance or Key instance, or None (the default) if the requested
        entities do not have a parent.
    :returns:
        A ``db.Model`` instance.
    """
    obj = model.get_by_id(id, parent=parent)
    if obj:
        return obj

    abort(404)


def get_by_key_name_or_404(model, key_name, parent=None):
    """Returns a model instance fetched by key name or raises a 404 Not Found
    error. Example::

        from tipfy import RequestHandler
        from tipfy.appengine.db import get_by_key_name_or_404
        from mymodels import Contact

        class EditContactHandler(RequestHandler):
            def get(self, **kwargs):
                contact = get_by_key_name_or_404(Contact,
                    kwargs['contact_key_name'])

                # ... continue processing contact ...

    This function derives from `Kay <http://code.google.com/p/kay-framework/>`_.

    :param model:
        A ``db.Model`` class to load an entity.
    :param key_name:
        A key name from a ``db.Key`` (a string).
    :param parent:
        The parent entity for the requested entities, as a Model
        instance or Key instance, or None (the default) if the requested
        entities do not have a parent.
    :returns:
        A ``db.Model`` instance.
    """
    obj = model.get_by_key_name(key_name, parent=parent)
    if obj:
        return obj

    abort(404)


def run_in_namespace(namespace, function, *args, **kwargs):
    """Executes a function in a given namespace, then returns back to the
    current namescape.

    :param namespace:
        Name of the namespace to run the function.
    :param function:
        Function to be executed in the given namespace.
    :param args:
        Arguments to be passed to the function.
    :param kwargs:
        Keyword arguments to be passed to the function.
    """
    current_namespace = namespace_manager.get_namespace()
    try:
        namespace_manager.set_namespace(namespace)
        return function(*args, **kwargs)
    finally:
        # Restore previous namespace.
        namespace_manager.set_namespace(current_namespace)


# Decorators.
def retry_on_timeout(retries=3, interval=1.0, exponent=2.0):
    """A decorator to retry a function that performs db operations in case a
    ``db.Timeout`` exception is raised. Example::

        from tipfy import RequestHandler
        from tipfy.appengine.db import retry_on_timeout
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

    This function derives from `Kay <http://code.google.com/p/kay-framework/>`_.

    :param retries:
        An integer value for the number of retries in case ``db.Timeout`` is
        raised.
    :param interval:
        A float value for the number of seconds between each interval.
    :param exponent:
        A float exponent to be applied to each retry interval.
        For example, if ``interval`` is set to 0.2 and exponent is 2.0,
        retries intervals will be in seconds: 0.2, 0.4, 0.8, etc.
    :returns:
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
    If not found, a ``NotFound`` exception is raised. Example::

        from tipfy import RequestHandler
        from tipfy.appengine.db import load_entity
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
        The keyword argument, passed by the routing system to the
        request handler, that contains the key, id or key_name of the entity
        to be loaded. For example, ``contact_key``, ``contact_id`` or
        ``contact_key_name``.
    :param kwarg_new:
        The new keyword argument to be passed to the request handler.
        This keyword is *added* to the arguments. If not set, uses kwarg_old
        as base, removing the fetch mode sufix. For example, ``contact``.
    :param fetch_mode:
        The fetch mode. Can be either ``key``, ``id`` or
        ``key_name``, to fetch using ``db.Model.get()``,
        ``db.Model.get_by_id()`` or ``db.Model.get_by_key_name()``,
        respectively. If not set, it will check if ``kwargs_old`` ends with
        ``_key``, ``_id`` or ``_key_name`` to guess the fetch mode.
    :returns:
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
        else:
            raise NotImplementedError('Invalid fetch_mode.')

    def decorator(func):
        def decorated(*args, **kwargs):
            entity = None
            key = kwargs.get(kwarg_old, None)
            if key is not None:
                if fetch_mode == 'key':
                    entity = get_or_404(key)
                elif fetch_mode == 'id':
                    entity = get_by_id_or_404(model, key)
                elif fetch_mode == 'key_name':
                    entity = get_by_key_name_or_404(model, key)

            kwargs[kwarg_new] = entity
            return func(*args, **kwargs)

        return decorated

    return decorator


def to_key(values):
    """Coerces a value or list of values to `db.Key` instances.

    :param value:
        A datastore key as string, `db.Model` or `db.Key` instances, or a list
        of them. None values of model instances that still don't have a key
        available will be appended to the result as None.
    :returns:
        A `db.Key` or a list of `db.Key` instances.
    """
    if values is None:
        return None

    if not isinstance(values, list):
        multiple = False
        values = [values]
    else:
        multiple = True

    res = []
    for value in values:
        if value is None:
            res.append(None)
        elif isinstance(value, db.Model):
            if value.has_key():
                res.append(value.key())
            else:
                res.append(None)
        elif isinstance(value, basestring):
            res.append(db.Key(value))
        elif isinstance(value, db.Key):
            res.append(value)
        else:
            raise datastore_errors.BadArgumentError('Expected model, key or '
                'string.')

    if multiple:
        return res

    return res[0]


class ModelMixin(object):
    """A base class for db.Model mixins. This allows to mix db properties
    from several base classes in a single model. For example::

        from google.appengine.ext import db

        from tipfy.appengine.db import ModelMixin

        class DateMixin(ModelMixin):
            created = db.DateTimeProperty(auto_now_add=True)
            updated = db.DateTimeProperty(auto_now=True)

        class AuditMixin(ModelMixin):
            created_by = db.UserProperty()
            updated_by = db.UserProperty()

        class Account(db.Model, DateMixin, AuditMixin):
            name = db.StringProperty()

        class SupportTicket(db.Model, DateMixin, AuditMixin):
            title = db.StringProperty()

        class Item(db.Model, DateMixin):
            name = db.StringProperty()
            description = db.StringProperty()

    Read more about it in the
    `tutorial <http://www.tipfy.org/wiki/cookbook/reusing-models-with-modelmixin/>`_.
    """
    __metaclass__ = db.PropertiedClass

    @classmethod
    def kind(self):
        """Need to implement this because it is called by PropertiedClass
        to register the kind name in _kind_map. We just return a dummy name.
        """
        return '__model_mixin__'


from tipfy.appengine.db.properties import *

# Old name
get_property_dict = get_entity_dict
