# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.model
"""
import unittest
from google.appengine.ext import db
from gaetestbed import DataStoreTestCase

from tipfy.ext.model import model_from_protobuf, model_to_protobuf, \
    populate_entity


class FooModel(db.Model):
    name = db.StringProperty(required=True)
    age = db.IntegerProperty(required=True)
    married = db.BooleanProperty(required=True)


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

        populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        self.assertEqual(entity_1.name, 'bar')
        self.assertEqual(entity_1.age, 20)
        self.assertEqual(entity_1.married, True)
        self.assertRaises(AttributeError, getattr, entity_1, 'city')

