# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.model
"""
import unittest
import hashlib

from google.appengine.ext import db
from gaetestbed import DataStoreTestCase

from tipfy import NotFound
from tipfy.ext.model import model_from_protobuf, model_to_protobuf, \
    populate_entity, get_by_key_name_or_404, get_by_id_or_404, get_or_404, \
    get_or_insert_with_flag, get_key, PickleProperty, SlugProperty, \
    EtagProperty, retry_on_timeout


class FooModel(db.Model):
    name = db.StringProperty(required=True)
    age = db.IntegerProperty()
    married = db.BooleanProperty()
    data = PickleProperty()
    slug = SlugProperty(name)
    etag = EtagProperty(name)


class FooExpandoModel(db.Expando):
    pass


class BarModel(db.Model):
    foo = db.ReferenceProperty(FooModel)


@retry_on_timeout(retries=3, interval=0.1)
def test_timeout_1(**kwargs):
    retry_count = kwargs.get('_retry_count')
    # Let it pass only in the last attempt
    if retry_count < 3:
        raise db.Timeout()

    return retry_count


@retry_on_timeout(retries=3, interval=0.1)
def test_timeout_2(**kwargs):
    retry_count = kwargs.get('_retry_count')
    # Let it pass only in the last attempt
    if retry_count < 3:
        raise db.Timeout()

    raise ValueError()

@retry_on_timeout(retries=3, interval=0.1)
def test_timeout_3(**kwargs):
    retry_count = kwargs.get('_retry_count')
    # Never Let it pass.
    if retry_count <= 3:
        raise db.Timeout()


class TestModel(DataStoreTestCase, unittest.TestCase):
    def test_one_model_to_and_from_protobuf(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        pb_1 = model_to_protobuf(entity_1)

        entity_1 = model_from_protobuf(pb_1)
        self.assertEqual(isinstance(entity_1, FooModel), True)
        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

    def test_several_models_to_and_from_protobuf(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()
        entity_2 = FooModel(name='bar', age=30, married=True)
        entity_2.put()
        entity_3 = FooModel(name='baz', age=45, married=False)
        entity_3.put()

        pbs = model_to_protobuf([entity_1, entity_2, entity_3])
        self.assertEqual(len(pbs), 3)
        pb_1, pb_2, pb_3 = pbs

        entity_1 = model_from_protobuf(pb_1)
        self.assertEqual(isinstance(entity_1, FooModel), True)
        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

        entity_2 = model_from_protobuf(pb_2)
        self.assertEqual(isinstance(entity_2, FooModel), True)
        self.assertEqual(entity_2.name, 'bar')
        self.assertEqual(entity_2.age, 30)
        self.assertEqual(entity_2.married, True)

        entity_3 = model_from_protobuf(pb_3)
        self.assertEqual(isinstance(entity_3, FooModel), True)
        self.assertEqual(entity_3.name, 'baz')
        self.assertEqual(entity_3.age, 45)
        self.assertEqual(entity_3.married, False)

    def test_populate_entity(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

        populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        self.assertEqual(entity_1.name, 'bar')
        self.assertEqual(entity_1.age, 20)
        self.assertEqual(entity_1.married, True)
        self.assertRaises(AttributeError, getattr, entity_1, 'city')

    def test_populate_expando_entity(self):
        entity_1 = FooExpandoModel(name='foo', age=15, married=False)
        entity_1.put()

        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

        populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        self.assertEqual(entity_1.name, 'bar')
        self.assertEqual(entity_1.age, 20)
        self.assertEqual(entity_1.married, True)
        self.assertRaises(AttributeError, getattr, entity_1, 'city')

    def test_get_by_key_name_or_404(self):
        entity_1 = FooModel(key_name='foo', name='foo', age=15, married=False)
        entity_1.put()

        entity = get_by_key_name_or_404(FooModel, 'foo')
        self.assertEqual(str(entity_1.key()), str(entity.key()))

        self.assertRaises(NotFound, get_by_key_name_or_404, FooModel, 'bar')

    def test_get_by_id_or_404(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        entity = get_by_id_or_404(FooModel, entity_1.key().id())
        self.assertEqual(str(entity_1.key()), str(entity.key()))

        self.assertRaises(NotFound, get_by_id_or_404, FooModel, -1)

    def test_get_or_404(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        entity = get_or_404(FooModel, entity_1.key())
        self.assertEqual(str(entity_1.key()), str(entity.key()))

        self.assertRaises(NotFound, get_or_404, FooModel, db.Key.from_path('FooModel', 'bar'))

    def test_get_or_insert_with_flag(self):
        entity, flag = get_or_insert_with_flag(FooModel, 'foo', name='foo', age=15, married=False)
        self.assertEqual(flag, True)
        self.assertEqual(entity.name, 'foo')
        self.assertEqual(entity.age, 15)
        self.assertEqual(entity.married, False)

        entity, flag = get_or_insert_with_flag(FooModel, 'foo', name='bar', age=30, married=True)
        self.assertEqual(flag, False)
        self.assertEqual(entity.name, 'foo')
        self.assertEqual(entity.age, 15)
        self.assertEqual(entity.married, False)

    def test_get_key(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()
        entity_1_key = str(entity_1.key())

        entity_2 = BarModel(key_name='first_bar', foo=entity_1)
        entity_2.put()

        entity_1.delete()
        entity_3 = BarModel.get_by_key_name('first_bar')
        # Won't resolve, but we can still get the key value.
        self.assertRaises(db.Error, getattr, entity_3, 'foo')
        self.assertEqual(str(get_key(entity_3, 'foo')), entity_1_key)

    def test_pickle_property(self):
        data_1 = {'foo': 'bar'}
        entity_1 = FooModel(key_name='foo', name='foo', data=data_1)
        entity_1.put()

        data_2 = [1, 2, 3, 'baz']
        entity_2 = FooModel(key_name='bar', name='bar', data=data_2)
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        self.assertEqual(data_1, entity_1.data)

        entity_2 = FooModel.get_by_key_name('bar')
        self.assertEqual(data_2, entity_2.data)

    def test_slug_property(self):
        entity_1 = FooModel(key_name='foo', name=u'Mary Björk')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'Tião Macalé')
        entity_2.put()


        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        self.assertEqual('mary-bjork', entity_1.slug)
        self.assertEqual('tiao-macale', entity_2.slug)

    def test_etag_property(self):
        entity_1 = FooModel(key_name='foo', name=u'Mary Björk')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'Tião Macalé')
        entity_2.put()


        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        self.assertEqual(hashlib.sha1(entity_1.name.encode('utf8')).hexdigest(), entity_1.etag)
        self.assertEqual(hashlib.sha1(entity_2.name.encode('utf8')).hexdigest(), entity_2.etag)

    def test_retry_on_timeout_1(self):
        retries = test_timeout_1()
        self.assertEqual(retries, 3)

    def test_retry_on_timeout_2(self):
        self.assertRaises(ValueError, test_timeout_2)

    def test_retry_on_timeout_3(self):
        self.assertRaises(db.Timeout, test_timeout_3)

