# -*- coding: utf-8 -*-
"""
    tipfy.model
    ~~~~~~~~~~~

    Model utilities.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from google.appengine.ext import db
from google.appengine.datastore import entity_pb

from tipfy.app import NotFound


def model_to_protobuf(models):
    """Converts one or more db.Model instances to encoded Protocol Buffers.
    Borrowed from http://blog.notdot.net/2009/9/Efficient-model-memcaching
    """
    if not models:
        return None
    elif isinstance(models, db.Model):
        return db.model_to_protobuf(models).Encode()
    else:
        return [db.model_to_protobuf(x).Encode() for x in models]


def model_from_protobuf(data):
    """Converts one or more encoded Protocol Buffers to db.Model instances.
    Borrowed from http://blog.notdot.net/2009/9/Efficient-model-memcaching
    """
    if not data:
        return None
    elif isinstance(data, str):
        return db.model_from_protobuf(entity_pb.EntityProto(data))
    else:
        return [db.model_from_protobuf(entity_pb.EntityProto(x)) for x in data]


def get_key(entity, prop_name):
    """Returns a encoded key from a ReferenceProperty without fetching the
    referenced entity.
    """
    getattr(entity.__class__, prop_name).get_value_for_datastore(entity)


def populate_entity(entity, **kwargs):
    """Sets a batch of property values in an entity."""
    properties = entity.properties()
    for key, value in kwargs.iteritems():
        if key in properties:
            setattr(entity, key, value)


def get_or_insert_with_flag(model, key_name, **kwargs):
    """Same as Model.get_or_insert(), but also returns a boolean flag
    indicating if the entity was inserted.
    """
    entity = model.get_by_key_name(key_name, parent=kwargs.get('parent'))
    if entity:
        return (entity, False)

    def txn():
        entity = model.get_by_key_name(key_name, parent=kwargs.get('parent'))
        if entity:
            return (entity, False)

        entity = model(key_name=key_name, **kwargs)
        entity.put()
        return (entity, True)

    return db.run_in_transaction(txn)


# db.Model convenience functions borrowed from Kay. See AUTHORS.txt for details.
def get_by_key_name_or_404(model, key_name):
    """Returns a model instance by key name or raises a 404 Not Found error."""
    obj = model.get_by_key_name(key_name)
    if not obj:
        raise NotFound()
    return obj


def get_by_id_or_404(model, id):
    """Returns a model instance by id or raises a 404 Not Found error."""
    obj = model.get_by_id(id)
    if not obj:
        raise NotFound()
    return obj


def get_or_404(model, key):
    """Returns a model instance by key or raises a 404 Not Found error."""
    obj = model.get(key)
    if not obj:
        raise NotFound()
    return obj
