# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.model
"""
import unittest

from google.appengine.ext import db
from gaetestbed import DataStoreTestCase
from nose.tools import assert_raises

from tipfy import NotFound
from tipfy.ext.model.form import model_form, ModelConverter, f, validators


class Contact(db.Model):
    name = db.StringProperty(required=True)
    city = db.StringProperty()
    age = db.IntegerProperty(required=True)
    is_admin = db.BooleanProperty(default=False)


class AllPropertiesModel(db.Model):
    """Property names are ugly, yes."""
    prop_string = db.StringProperty()
    prop_byte_string = db.ByteStringProperty()
    prop_boolean = db.BooleanProperty()
    prop_integer = db.IntegerProperty()
    prop_float = db.FloatProperty()
    prop_date_time = db.DateTimeProperty()
    prop_date = db.DateProperty()
    prop_time = db.TimeProperty()
    prop_list = db.ListProperty(int)
    prop_string_list = db.StringListProperty()
    prop_reference = db.ReferenceProperty()
    prop_self_refeference = db.SelfReferenceProperty()
    prop_user = db.UserProperty()
    prop_blob = db.BlobProperty()
    prop_text = db.TextProperty()
    prop_category = db.CategoryProperty()
    prop_link = db.LinkProperty()
    prop_email = db.EmailProperty()
    prop_geo_pt = db.GeoPtProperty()
    prop_im = db.IMProperty()
    prop_phone_number = db.PhoneNumberProperty()
    prop_postal_address = db.PostalAddressProperty()
    prop_rating = db.RatingProperty()


class DateTimeModel(db.Model):
    prop_date_time_1 = db.DateTimeProperty()
    prop_date_time_2 = db.DateTimeProperty(auto_now=True)
    prop_date_time_3 = db.DateTimeProperty(auto_now_add=True)

    prop_date_1 = db.DateProperty()
    prop_date_2 = db.DateProperty(auto_now=True)
    prop_date_3 = db.DateProperty(auto_now_add=True)

    prop_time_1 = db.TimeProperty()
    prop_time_2 = db.TimeProperty(auto_now=True)
    prop_time_3 = db.TimeProperty(auto_now_add=True)


class Author(db.Model):
    name = db.StringProperty(required=True)

class Book(db.Model):
    author = db.ReferenceProperty(Author)


class TestModelForm(DataStoreTestCase, unittest.TestCase):
    def test_model_form_basic(self):
        form_class = model_form(Contact)

        assert hasattr(form_class, 'name')
        assert hasattr(form_class, 'age')
        assert hasattr(form_class, 'city')
        assert hasattr(form_class, 'is_admin')

        form = form_class()
        assert isinstance(form.name, f.TextField)
        assert isinstance(form.city, f.TextField)
        assert isinstance(form.age, f.IntegerField)
        assert isinstance(form.is_admin, f.BooleanField)

    def test_required_field(self):
        form_class = model_form(Contact)

        form = form_class()
        assert form.name.flags.required is True
        assert form.city.flags.required is False
        assert form.age.flags.required is True
        assert form.is_admin.flags.required is False

    def test_default_value(self):
        form_class = model_form(Contact)

        form = form_class()
        assert form.name._default is None
        assert form.city._default is None
        assert form.age._default is None
        assert form.is_admin._default is False

    def test_model_form_only(self):
        form_class = model_form(Contact, only=['name', 'age'])

        assert hasattr(form_class, 'name')
        assert hasattr(form_class, 'city') is False
        assert hasattr(form_class, 'age')
        assert hasattr(form_class, 'is_admin') is False

        form = form_class()
        assert isinstance(form.name, f.TextField)
        assert isinstance(form.age, f.IntegerField)

    def test_model_form_exclude(self):
        form_class = model_form(Contact, exclude=['is_admin'])

        assert hasattr(form_class, 'name')
        assert hasattr(form_class, 'city')
        assert hasattr(form_class, 'age')
        assert hasattr(form_class, 'is_admin') is False

        form = form_class()
        assert isinstance(form.name, f.TextField)
        assert isinstance(form.city, f.TextField)
        assert isinstance(form.age, f.IntegerField)

    def test_not_implemented_properties(self):
        # This should not raise NotImplementedError.
        form = model_form(AllPropertiesModel)

        # These properties should not be included in the form.
        assert_raises(AttributeError, getattr, model_form, 'prop_list')
        assert_raises(AttributeError, getattr, model_form, 'prop_user')
        assert_raises(AttributeError, getattr, model_form, 'prop_geo_pt')
        assert_raises(AttributeError, getattr, model_form, 'prop_im')

    def test_datetime_model(self):
        """Fields marked as auto_add / auto_add_now should not be included."""
        form_class = model_form(DateTimeModel)

        assert hasattr(form_class, 'prop_date_time_1')
        assert hasattr(form_class, 'prop_date_time_2') is False
        assert hasattr(form_class, 'prop_date_time_3') is False

        assert hasattr(form_class, 'prop_date_1')
        assert hasattr(form_class, 'prop_date_2') is False
        assert hasattr(form_class, 'prop_date_3') is False

        assert hasattr(form_class, 'prop_time_1')
        assert hasattr(form_class, 'prop_time_2') is False
        assert hasattr(form_class, 'prop_time_3') is False

    def test_populate_form(self):
        entity = Contact(key_name='test', name='John', city='Yukon', age=25, is_admin=True)
        entity.put()

        obj = Contact.get_by_key_name('test')
        form_class = model_form(Contact)

        form = form_class(obj=obj)
        assert form.name.data == 'John'
        assert form.city.data == 'Yukon'
        assert form.age.data == 25
        assert form.is_admin.data is True

    def test_field_attributes(self):
        form_class = model_form(Contact, field_args={
            'name': {
                'label': 'Full name',
                'description': 'Your name',
            },
            'age': {
                'label': 'Age',
                'validators': [validators.NumberRange(min=14, max=99)],
            },
            'city': {
                'label': 'City',
                'description': 'The city in which you live, not the one in which you were born.',
            },
            'is_admin': {
                'label': 'Administrative rights',
            },
        })
        form = form_class()

        assert form.name.label.text == 'Full name'
        assert form.name.description == 'Your name'

        assert form.age.label.text == 'Age'

        assert form.city.label.text == 'City'
        assert form.city.description == 'The city in which you live, not the one in which you were born.'

        assert form.is_admin.label.text == 'Administrative rights'

    def test_reference_property(self):
        keys = []
        for name in ['foo', 'bar', 'baz']:
            author = Author(name=name)
            author.put()
            keys.append(str(author.key()))

        form_class = model_form(Book)
        form = form_class()

        choices = []
        i = 0
        for key, name, value in form.author.iter_choices():
            assert key == keys[i]
            i += 1
