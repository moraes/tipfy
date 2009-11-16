# -*- coding: utf-8 -*-
"""
    tipfy.ext.model.forms
    ~~~~~~~~~~~~~~~~~~~~~

    Form generation utilities for db.Model classes.

    Example usage:

        from google.appengine.ext import db
        from tipfy.ext.model.form import model_form

        # Define a model.
        class MyModel(db.Model):
            name = db.StringProperty(default='some default value')
            number = db.IntegerProperty(required=True)

        # Generate a form based on the model.
        MyModelForm = model_form(MyModel)

        # Add a record.
        new_entity = MyModel(key_name='test', name='Foo Test Name', number=7)
        new_entity.put()

        # Get a form populated with entity data.
        entity = MyModel.get_by_key_name('test')
        form = MyModelForm(obj=entity)

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from wtforms import widgets
from wtforms import fields as f
from wtforms import Form
from wtforms import validators


class StringListPropertyField(f.TextAreaField):
    def process_data(self, value):
        if isinstance(value, list):
            value = '\n'.join(value)

        self.data = value

    def populate_obj(self, obj, name):
        if isinstance(self.data, basestring):
            value = self.data.splitlines()
        else:
            value = []

        setattr(obj, name, value)


def get_TextField(kwargs):
    # StringProperty limit: 500 bytes.
    kwargs['validators'].append(validators.length(max=500))
    return f.TextField(**kwargs)


def get_IntegerField(kwargs):
    # IntegerProperty limit.
    kwargs['validators'].append(validators.NumberRange(min=0x8000000000000000,
        max=0x7fffffffffffffff))
    return f.IntegerField(**kwargs)


def convert_StringProperty(model, prop, kwargs):
    if prop.multiline:
        kwargs['validators'].append(validators.length(max=500))
        return f.TextAreaField(**kwargs)
    else:
        return get_TextField(kwargs)


def convert_ByteStringProperty(model, prop, kwargs):
    raise NotImplemented()


def convert_BooleanProperty(model, prop, kwargs):
    return f.BooleanField(**kwargs)


def convert_IntegerProperty(model, prop, kwargs):
    return get_IntegerField(kwargs)


def convert_FloatProperty(model, prop, kwargs):
    return get_TextField(kwargs)


def convert_DateTimeProperty(model, prop, kwargs):
    if prop.auto_now or prop.auto_now_add:
        return None
    return f.DateTimeField(format='%Y-%m-%d %H-%M-%S', **kwargs)


def convert_DateProperty(model, prop, kwargs):
    if prop.auto_now or prop.auto_now_add:
        return None
    return f.DateTimeField(format='%Y-%m-%d', **kwargs)


def convert_TimeProperty(model, prop, kwargs):
    if prop.auto_now or prop.auto_now_add:
        return None
    return f.DateTimeField(format='%H-%M-%S', **kwargs)


def convert_ListProperty(model, prop, kwargs):
    raise NotImplemented()


def convert_StringListProperty(model, prop, kwargs):
    return StringListPropertyField(**kwargs)


def convert_ReferenceProperty(model, prop, kwargs):
    raise NotImplemented()


def convert_SelfReferenceProperty(model, prop, kwargs):
    raise NotImplemented()


def convert_UserProperty(model, prop, kwargs):
    raise NotImplemented()


def convert_BlobProperty(model, prop, kwargs):
    return f.FileField(**kwargs)


def convert_TextProperty(model, prop, kwargs):
    return f.TextAreaField(**kwargs)


def convert_CategoryProperty(model, prop, kwargs):
    raise NotImplemented()


def convert_LinkProperty(model, prop, kwargs):
    kwargs['validators'].append(validators.url())
    return get_TextField(kwargs)


def convert_EmailProperty(model, prop, kwargs):
    kwargs['validators'].append(validators.email())
    return get_TextField(kwargs)


def convert_GeoPtProperty(model, prop, kwargs):
    raise NotImplemented()


def convert_IMProperty(model, prop, kwargs):
    raise NotImplemented()


def convert_PhoneNumberProperty(model, prop, kwargs):
    return get_TextField(kwargs)


def convert_PostalAddressProperty(model, prop, kwargs):
    return get_TextField(kwargs)


def convert_RatingProperty(model, prop, kwargs):
    raise NotImplemented()


class ModelConverter(object):
    """Converts properties from a db.Model class to form fields."""
    default_converters = {
        'StringProperty':        convert_StringProperty,
        'ByteStringProperty':    convert_ByteStringProperty,
        'BooleanProperty':       convert_BooleanProperty,
        'IntegerProperty':       convert_IntegerProperty,
        'FloatProperty':         convert_FloatProperty,
        'DateTimeProperty':      convert_DateTimeProperty,
        'DateProperty':          convert_DateProperty,
        'TimeProperty':          convert_TimeProperty,
        'ListProperty':          convert_ListProperty,
        'StringListProperty':    convert_StringListProperty,
        'ReferenceProperty':     convert_ReferenceProperty,
        'SelfReferenceProperty': convert_SelfReferenceProperty,
        'UserProperty':          convert_UserProperty,
        'BlobProperty':          convert_BlobProperty,
        'TextProperty':          convert_TextProperty,
        'CategoryProperty':      convert_CategoryProperty,
        'LinkProperty':          convert_LinkProperty,
        'EmailProperty':         convert_EmailProperty,
        'GeoPtProperty':         convert_GeoPtProperty,
        'IMProperty':            convert_IMProperty,
        'PhoneNumberProperty':   convert_PhoneNumberProperty,
        'PostalAddressProperty': convert_PostalAddressProperty,
        'RatingProperty':        convert_RatingProperty,
    }

    def __init__(self, converters=None):
        self.converters = converters or self.default_converters

    def convert(self, model, prop, field_args):
        kwargs = {
            'label': prop.name,
            'default': prop.default_value(),
            'validators': [],
        }
        if field_args:
            kwargs.update(field_args)

        if prop.required:
            kwargs['validators'].append(validators.required())

        if prop.choices:
            # Use choices in a select field.
            kwargs['choices'] = [(v, v) for v in prop.choices]
            return f.SelectField(**kwargs)
        else:
            method = self.converters.get(type(prop).__name__, None)
            if method is not None:
                return method(model, prop, kwargs)


def model_form(model, base_class=Form, converter=None, only=None, exclude=None,
    field_args=None):
    """Creates a wtforms form for a given db.Model class.

    :param model:
        The ``db.Model`` class to generate a form for.
    :param base_class:
        Base form class to extend from. Must be a ``wtforms.Form`` subclass.
    :param converter:
        A converter to generate the fields based on the model properties. If
        not set, ``ModelConverter`` will be used.
    :param only:
        An optional iterable with the property names to include in the form.
        Only these properties will have fields.
    :param exclude:
        An optional iterable with the property names to not include in the form.
        All other properties will have fields.
    :param field_args:
        An optional dictionary of field names mapping to a dictionary of
        arguments used to construct the field object.
    """
    converter = converter or ModelConverter()
    field_args = field_args or {}

    # Get the field names we want to include or exclude, starting with the
    # full list of model properties.
    props = model.properties()
    field_names = props.keys()
    if only:
        field_names = list(f for f in only if f in field_names)
    elif exclude:
        field_names = list(f for f in field_names if f not in exclude)

    # Create all fields.
    field_dict = {}
    for name in field_names:
        field = converter.convert(model, props[name], field_args.get(name))
        if field is not None:
            field_dict[name] = field

    # Return a dynamically created new class, extending from base_class and
    # including the created fields as properties.
    return type(model.kind() + 'Form', (base_class,), field_dict)
