# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.model
"""
import unittest

from google.appengine.ext import db
from gaetestbed import DataStoreTestCase

from tipfy import NotFound
from tipfy.ext.model.form import model_form, ModelConverter, f


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


class TestModelForm(DataStoreTestCase, unittest.TestCase):
    def test_model_form_basic(self):
        form_class = model_form(Contact)

        self.assertEqual(hasattr(form_class, 'name'), True)
        self.assertEqual(hasattr(form_class, 'age'), True)
        self.assertEqual(hasattr(form_class, 'city'), True)
        self.assertEqual(hasattr(form_class, 'is_admin'), True)

        form = form_class()
        self.assertEqual(isinstance(form.name, f.TextField), True)
        self.assertEqual(isinstance(form.city, f.TextField), True)
        self.assertEqual(isinstance(form.age, f.IntegerField), True)
        self.assertEqual(isinstance(form.is_admin, f.BooleanField), True)

    def test_required_field(self):
        form_class = model_form(Contact)

        form = form_class()
        self.assertEqual(form.name.flags.required, True)
        self.assertEqual(form.city.flags.required, False)
        self.assertEqual(form.age.flags.required, True)
        self.assertEqual(form.is_admin.flags.required, False)

    def test_default_value(self):
        form_class = model_form(Contact)

        form = form_class()
        self.assertEqual(form.name._default, None)
        self.assertEqual(form.city._default, None)
        self.assertEqual(form.age._default, None)
        self.assertEqual(form.is_admin._default, False)

    def test_model_form_only(self):
        form_class = model_form(Contact, only=['name', 'age'])

        self.assertEqual(hasattr(form_class, 'name'), True)
        self.assertEqual(hasattr(form_class, 'city'), False)
        self.assertEqual(hasattr(form_class, 'age'), True)
        self.assertEqual(hasattr(form_class, 'is_admin'), False)

        form = form_class()
        self.assertEqual(isinstance(form.name, f.TextField), True)
        self.assertEqual(isinstance(form.age, f.IntegerField), True)

    def test_model_form_exclude(self):
        form_class = model_form(Contact, exclude=['is_admin'])

        self.assertEqual(hasattr(form_class, 'name'), True)
        self.assertEqual(hasattr(form_class, 'city'), True)
        self.assertEqual(hasattr(form_class, 'age'), True)
        self.assertEqual(hasattr(form_class, 'is_admin'), False)

        form = form_class()
        self.assertEqual(isinstance(form.name, f.TextField), True)
        self.assertEqual(isinstance(form.city, f.TextField), True)
        self.assertEqual(isinstance(form.age, f.IntegerField), True)

    def test_not_implemented_properties(self):
        self.assertRaises(NotImplementedError, model_form, AllPropertiesModel)
        self.assertRaises(NotImplementedError, model_form, AllPropertiesModel, only=('prop_list',))
        self.assertRaises(NotImplementedError, model_form, AllPropertiesModel, only=('prop_reference',))
        self.assertRaises(NotImplementedError, model_form, AllPropertiesModel, only=('prop_self_refeference',))
        self.assertRaises(NotImplementedError, model_form, AllPropertiesModel, only=('prop_user',))
        self.assertRaises(NotImplementedError, model_form, AllPropertiesModel, only=('prop_geo_pt',))
        self.assertRaises(NotImplementedError, model_form, AllPropertiesModel, only=('prop_im',))

        form = model_form(AllPropertiesModel, exclude=('prop_list', 'prop_reference',
            'prop_self_refeference', 'prop_user', 'prop_geo_pt', 'prop_im'))

    def test_datetime_model(self):
        """Fields marked as auto_add / auto_add_now should not be included."""
        form_class = model_form(DateTimeModel)

        self.assertEqual(hasattr(form_class, 'prop_date_time_1'), True)
        self.assertEqual(hasattr(form_class, 'prop_date_time_2'), False)
        self.assertEqual(hasattr(form_class, 'prop_date_time_3'), False)

        self.assertEqual(hasattr(form_class, 'prop_date_1'), True)
        self.assertEqual(hasattr(form_class, 'prop_date_2'), False)
        self.assertEqual(hasattr(form_class, 'prop_date_3'), False)

        self.assertEqual(hasattr(form_class, 'prop_time_1'), True)
        self.assertEqual(hasattr(form_class, 'prop_time_2'), False)
        self.assertEqual(hasattr(form_class, 'prop_time_3'), False)
