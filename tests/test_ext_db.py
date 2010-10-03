# -*- coding: utf-8 -*-
"""
    Tests for tipfyext.appengine.db
"""
import unittest
import hashlib

from google.appengine.ext import db
from google.appengine.api import datastore_errors
from gaetestbed import DataStoreTestCase

from werkzeug.exceptions import NotFound

from tipfyext.appengine import db as ext_db


class FooModel(db.Model):
    name = db.StringProperty(required=True)
    name2 = db.StringProperty()
    age = db.IntegerProperty()
    married = db.BooleanProperty()
    data = ext_db.PickleProperty()
    slug = ext_db.SlugProperty(name)
    slug2 = ext_db.SlugProperty(name2, default='some-default-value', max_length=20)
    etag = ext_db.EtagProperty(name)
    etag2 = ext_db.EtagProperty(name2)
    somekey = ext_db.KeyProperty()


class FooExpandoModel(db.Expando):
    pass


class BarModel(db.Model):
    foo = db.ReferenceProperty(FooModel)


class JsonModel(db.Model):
    data = ext_db.JsonProperty()


class TimezoneModel(db.Model):
    data = ext_db.TimezoneProperty()


@ext_db.retry_on_timeout(retries=3, interval=0.1)
def test_timeout_1(**kwargs):
    counter = kwargs.get('counter')

    # Let it pass only in the last attempt
    if counter[0] < 3:
        counter[0] += 1
        raise db.Timeout()


@ext_db.retry_on_timeout(retries=5, interval=0.1)
def test_timeout_2(**kwargs):
    counter = kwargs.get('counter')

    # Let it pass only in the last attempt
    if counter[0] < 5:
        counter[0] += 1
        raise db.Timeout()

    raise ValueError()


@ext_db.retry_on_timeout(retries=2, interval=0.1)
def test_timeout_3(**kwargs):
    # Never let it pass.
    counter = kwargs.get('counter')
    counter[0] += 1
    raise db.Timeout()


class TestModel(DataStoreTestCase, unittest.TestCase):
    def setUp(self):
        DataStoreTestCase.setUp(self)

    def test_no_protobuf_from_entity(self):
        res_1 = ext_db.get_entity_from_protobuf([])
        self.assertEqual(res_1, None)
        res_2 = ext_db.get_protobuf_from_entity(None)
        self.assertEqual(res_2, None)

    def test_no_entity_from_protobuf(self):
        res_1 = ext_db.get_entity_from_protobuf([])
        self.assertEqual(res_1, None)

    def test_one_model_to_and_from_protobuf(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        pb_1 = ext_db.get_protobuf_from_entity(entity_1)

        entity_1 = ext_db.get_entity_from_protobuf(pb_1)
        self.assertEqual(isinstance(entity_1, FooModel), True)
        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

    def test_many_models_to_and_from_protobuf(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()
        entity_2 = FooModel(name='bar', age=30, married=True)
        entity_2.put()
        entity_3 = FooModel(name='baz', age=45, married=False)
        entity_3.put()

        pbs = ext_db.get_protobuf_from_entity([entity_1, entity_2, entity_3])
        self.assertEqual(len(pbs), 3)

        entity_1, entity_2, entity_3 = ext_db.get_entity_from_protobuf(pbs)
        self.assertEqual(isinstance(entity_1, FooModel), True)
        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

        self.assertEqual(isinstance(entity_2, FooModel), True)
        self.assertEqual(entity_2.name, 'bar')
        self.assertEqual(entity_2.age, 30)
        self.assertEqual(entity_2.married, True)

        self.assertEqual(isinstance(entity_3, FooModel), True)
        self.assertEqual(entity_3.name, 'baz')
        self.assertEqual(entity_3.age, 45)
        self.assertEqual(entity_3.married, False)

    def test_get_protobuf_from_entity_using_dict(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()
        entity_2 = FooModel(name='bar', age=30, married=True)
        entity_2.put()
        entity_3 = FooModel(name='baz', age=45, married=False)
        entity_3.put()

        entity_dict = {'entity_1': entity_1, 'entity_2': entity_2, 'entity_3': entity_3,}

        pbs = ext_db.get_protobuf_from_entity(entity_dict)

        entities = ext_db.get_entity_from_protobuf(pbs)
        entity_1 = entities['entity_1']
        entity_2 = entities['entity_2']
        entity_3 = entities['entity_3']

        self.assertEqual(isinstance(entity_1, FooModel), True)
        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

        self.assertEqual(isinstance(entity_2, FooModel), True)
        self.assertEqual(entity_2.name, 'bar')
        self.assertEqual(entity_2.age, 30)
        self.assertEqual(entity_2.married, True)

        self.assertEqual(isinstance(entity_3, FooModel), True)
        self.assertEqual(entity_3.name, 'baz')
        self.assertEqual(entity_3.age, 45)
        self.assertEqual(entity_3.married, False)

    def test_get_or_insert_with_flag(self):
        entity, flag = ext_db.get_or_insert_with_flag(FooModel, 'foo', name='foo', age=15, married=False)
        self.assertEqual(flag, True)
        self.assertEqual(entity.name, 'foo')
        self.assertEqual(entity.age, 15)
        self.assertEqual(entity.married, False)

        entity, flag = ext_db.get_or_insert_with_flag(FooModel, 'foo', name='bar', age=30, married=True)
        self.assertEqual(flag, False)
        self.assertEqual(entity.name, 'foo')
        self.assertEqual(entity.age, 15)
        self.assertEqual(entity.married, False)

    def test_get_reference_key(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()
        entity_1_key = str(entity_1.key())

        entity_2 = BarModel(key_name='first_bar', foo=entity_1)
        entity_2.put()

        entity_1.delete()
        entity_3 = BarModel.get_by_key_name('first_bar')
        # Won't resolve, but we can still get the key value.
        self.assertRaises(db.Error, getattr, entity_3, 'foo')
        self.assertEqual(str(ext_db.get_reference_key(entity_3, 'foo')), entity_1_key)

    def test_get_reference_key_2(self):
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
        self.assertEqual(str(ext_db.get_reference_key(fetched_book, 'author')), str(author.key()))

    #===========================================================================
    # ext_db.populate_entity
    #===========================================================================
    def test_populate_entity(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

        ext_db.populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        self.assertEqual(entity_1.name, 'bar')
        self.assertEqual(entity_1.age, 20)
        self.assertEqual(entity_1.married, True)

    def test_populate_entity_2(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

        ext_db.populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        self.assertRaises(AttributeError, getattr, entity_1, 'city')

    def test_populate_expando_entity(self):
        entity_1 = FooExpandoModel(name='foo', age=15, married=False)
        entity_1.put()

        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

        ext_db.populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        self.assertEqual(entity_1.name, 'bar')
        self.assertEqual(entity_1.age, 20)
        self.assertEqual(entity_1.married, True)

    def test_populate_expando_entity_2(self):
        entity_1 = FooExpandoModel(name='foo', age=15, married=False)
        entity_1.put()

        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

        ext_db.populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        self.assertRaises(AttributeError, getattr, entity_1, 'city')


    #===========================================================================
    # ext_db.get_entity_dict
    #===========================================================================
    def test_get_entity_dict(self):
        class MyModel(db.Model):
            animal = db.StringProperty()
            species = db.IntegerProperty()
            description = db.TextProperty()

        entity = MyModel(animal='duck', species=12,
            description='A duck, a bird that swims well.')
        values = ext_db.get_entity_dict(entity)

        self.assertEqual(values, {
            'animal': 'duck',
            'species': 12,
            'description': 'A duck, a bird that swims well.',
        })

    def test_get_entity_dict_multiple(self):
        class MyModel(db.Model):
            animal = db.StringProperty()
            species = db.IntegerProperty()
            description = db.TextProperty()

        entity = MyModel(animal='duck', species=12,
            description='A duck, a bird that swims well.')
        entity2 = MyModel(animal='bird', species=7,
            description='A bird, an animal that flies well.')
        values = ext_db.get_entity_dict([entity, entity2])

        self.assertEqual(values, [
            {
                'animal': 'duck',
                'species': 12,
                'description': 'A duck, a bird that swims well.',
            },
            {
                'animal': 'bird',
                'species': 7,
                'description': 'A bird, an animal that flies well.',
            }
        ])

    def test_get_entity_dict_with_expando(self):
        class MyModel(db.Expando):
            animal = db.StringProperty()
            species = db.IntegerProperty()
            description = db.TextProperty()

        entity = MyModel(animal='duck', species=12,
            description='A duck, a bird that swims well.',
            most_famous='Daffy Duck')
        values = ext_db.get_entity_dict(entity)

        self.assertEqual(values, {
            'animal': 'duck',
            'species': 12,
            'description': 'A duck, a bird that swims well.',
            'most_famous': 'Daffy Duck',
        })

    #===========================================================================
    # get..._or_404
    #===========================================================================
    def test_get_by_key_name_or_404(self):
        entity_1 = FooModel(key_name='foo', name='foo', age=15, married=False)
        entity_1.put()

        entity = ext_db.get_by_key_name_or_404(FooModel, 'foo')
        self.assertEqual(str(entity.key()), str(entity_1.key()))

    def test_get_by_key_name_or_404_2(self):
        self.assertRaises(NotFound, ext_db.get_by_key_name_or_404, FooModel, 'bar')

    def test_get_by_id_or_404(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        entity = ext_db.get_by_id_or_404(FooModel, entity_1.key().id())
        self.assertEqual(str(entity.key()), str(entity_1.key()))

    def test_get_by_id_or_404_2(self):
        self.assertRaises(NotFound, ext_db.get_by_id_or_404, FooModel, -1)

    def test_get_or_404(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        entity = ext_db.get_or_404(entity_1.key())
        self.assertEqual(str(entity.key()), str(entity_1.key()))

    def test_get_or_404_2(self):
        self.assertRaises(NotFound, ext_db.get_or_404, db.Key.from_path('FooModel', 'bar'))

    def test_get_or_404_3(self):
        self.assertRaises(NotFound, ext_db.get_or_404, 'this, not a valid key')

    #===========================================================================
    # db.Property
    #===========================================================================
    def test_pickle_property(self):
        data_1 = {'foo': 'bar'}
        entity_1 = FooModel(key_name='foo', name='foo', data=data_1)
        entity_1.put()

        data_2 = [1, 2, 3, 'baz']
        entity_2 = FooModel(key_name='bar', name='bar', data=data_2)
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        self.assertEqual(entity_1.data, data_1)

        entity_2 = FooModel.get_by_key_name('bar')
        self.assertEqual(entity_2.data, data_2)

    def test_slug_property(self):
        entity_1 = FooModel(key_name='foo', name=u'Mary Björk')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'Tião Macalé')
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        self.assertEqual(entity_1.slug, 'mary-bjork')
        self.assertEqual(entity_2.slug, 'tiao-macale')

    def test_slug_property2(self):
        entity_1 = FooModel(key_name='foo', name=u'---')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'___')
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        self.assertEqual(entity_1.slug, None)
        self.assertEqual(entity_2.slug, None)

    def test_slug_property3(self):
        entity_1 = FooModel(key_name='foo', name=u'---', name2=u'---')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'___', name2=u'___')
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        self.assertEqual(entity_1.slug2, 'some-default-value')
        self.assertEqual(entity_2.slug2, 'some-default-value')

    def test_slug_property4(self):
        entity_1 = FooModel(key_name='foo', name=u'---', name2=u'Some really very big and maybe enormous string')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'___', name2=u'abcdefghijklmnopqrstuwxyz')
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        self.assertEqual(entity_1.slug2, 'some-really-very-big')
        self.assertEqual(entity_2.slug2, 'abcdefghijklmnopqrst')

    def test_etag_property(self):
        entity_1 = FooModel(key_name='foo', name=u'Mary Björk')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'Tião Macalé')
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        self.assertEqual(entity_1.etag, hashlib.sha1(entity_1.name.encode('utf8')).hexdigest())
        self.assertEqual(entity_2.etag, hashlib.sha1(entity_2.name.encode('utf8')).hexdigest())

    def test_etag_property2(self):
        entity_1 = FooModel(key_name='foo', name=u'Mary Björk')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'Tião Macalé')
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        self.assertEqual(entity_1.etag2, None)
        self.assertEqual(entity_2.etag2, None)

    def test_json_property(self):
        entity_1 = JsonModel(key_name='foo', data={'foo': 'bar'})
        entity_1.put()

        entity_1 = JsonModel.get_by_key_name('foo')
        self.assertEqual(entity_1.data, {'foo': 'bar'})

    def test_json_property2(self):
        self.assertRaises(db.BadValueError, JsonModel, key_name='foo', data='foo')

    def test_timezone_property(self):
        zone = 'America/Chicago'
        entity_1 = TimezoneModel(key_name='foo', data=zone)
        entity_1.put()

        entity_1 = TimezoneModel.get_by_key_name('foo')
        self.assertEqual(entity_1.data, ext_db.pytz.timezone(zone))

    def test_timezone_property2(self):
        self.assertRaises(db.BadValueError, TimezoneModel, key_name='foo', data=[])

    def test_timezone_property3(self):
        self.assertRaises(ext_db.pytz.UnknownTimeZoneError, TimezoneModel, key_name='foo', data='foo')

    def test_key_property(self):
        key = db.Key.from_path('Bar', 'bar-key')
        entity_1 = FooModel(name='foo', key_name='foo', somekey=key)
        entity_1.put()

        entity_1 = FooModel.get_by_key_name('foo')
        self.assertEqual(entity_1.somekey, key)

    def test_key_property2(self):
        key = db.Key.from_path('Bar', 'bar-key')
        entity_1 = FooModel(name='foo', key_name='foo', somekey=str(key))
        entity_1.put()

        entity_1 = FooModel.get_by_key_name('foo')
        self.assertEqual(entity_1.somekey, key)

    def test_key_property3(self):
        key = db.Key.from_path('Bar', 'bar-key')
        entity_1 = FooModel(name='foo', key_name='foo', somekey=str(key))
        entity_1.put()

        entity_2 = FooModel(name='bar', key_name='bar', somekey=entity_1)
        entity_2.put()

        entity_2 = FooModel.get_by_key_name('bar')
        self.assertEqual(entity_2.somekey, entity_1.key())

    def test_key_property4(self):
        key = db.Key.from_path('Bar', 'bar-key')
        entity_1 = FooModel(name='foo', somekey=str(key))
        self.assertRaises(db.BadValueError, FooModel, name='bar', key_name='bar', somekey=entity_1)

    def test_key_property5(self):
        self.assertRaises(TypeError, FooModel, name='foo', key_name='foo', somekey=['foo'])

    def test_key_property6(self):
        self.assertRaises(datastore_errors.BadKeyError, FooModel, name='foo', key_name='foo', somekey='foo')

    #===========================================================================
    # @ext_db.retry_on_timeout
    #===========================================================================
    def test_retry_on_timeout_1(self):
        counter = [0]
        test_timeout_1(counter=counter)
        self.assertEqual(counter[0], 3)

    def test_retry_on_timeout_2(self):
        counter = [0]
        self.assertRaises(ValueError, test_timeout_2, counter=counter)
        self.assertEqual(counter[0], 5)

    def test_retry_on_timeout_3(self):
        counter = [0]
        self.assertRaises(db.Timeout, test_timeout_3, counter=counter)
        self.assertEqual(counter[0], 3)

    #===========================================================================
    # @ext_db.load_entity
    #===========================================================================
    def test_load_entity_with_key(self):
        @ext_db.load_entity(FooModel, 'foo_key', 'foo', 'key')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(name='foo')
        foo.put()

        loaded_foo = get(foo_key=str(foo.key()))
        self.assertEqual(str(loaded_foo.key()), str(foo.key()))
        self.assertEqual(get(foo_key=None), None)

    def test_load_entity_with_key_2(self):
        @ext_db.load_entity(FooModel, 'foo_key', 'foo', 'key')
        def get(*args, **kwargs):
            return kwargs['foo']

        self.assertRaises(NotFound, get, foo_key=str(db.Key.from_path('FooModel', 'bar')))

    def test_load_entity_with_id(self):
        @ext_db.load_entity(FooModel, 'foo_id', 'foo', 'id')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(name='foo')
        foo.put()

        loaded_foo = get(foo_id=foo.key().id())
        self.assertEqual(str(loaded_foo.key()), str(foo.key()))

    def test_load_entity_with_id_2(self):
        @ext_db.load_entity(FooModel, 'foo_id', 'foo', 'id')
        def get(*args, **kwargs):
            return kwargs['foo']

        self.assertRaises(NotFound, get, foo_id=-1)

    def test_load_entity_with_key_name(self):
        @ext_db.load_entity(FooModel, 'foo_key_name', 'foo', 'key_name')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(key_name='foo', name='foo')
        foo.put()

        loaded_foo = get(foo_key_name='foo')
        self.assertEqual(str(loaded_foo.key()), str(foo.key()))

    def test_load_entity_with_key_name_2(self):
        @ext_db.load_entity(FooModel, 'foo_key_name', 'foo', 'key_name')
        def get(*args, **kwargs):
            return kwargs['foo']

        self.assertRaises(NotFound, get, foo_key_name='bar')

    def test_load_entity_with_key_with_guessed_fetch_mode(self):
        @ext_db.load_entity(FooModel, 'foo_key')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(name='foo')
        foo.put()

        loaded_foo = get(foo_key=str(foo.key()))
        self.assertEqual(str(loaded_foo.key()), str(foo.key()))
        self.assertEqual(get(foo_key=None), None)

    def test_load_entity_with_key_with_impossible_fetch_mode(self):
        def test():
            @ext_db.load_entity(FooModel, 'foo_bar')
            def get(*args, **kwargs):
                return kwargs['foo']

        self.assertRaises(NotImplementedError, test)

    #===========================================================================
    # ext_db.run_in_namespace
    #===========================================================================
    def test_run_in_namespace(self):
        class MyModel(db.Model):
            name = db.StringProperty()

        def create_entity(name):
            entity = MyModel(key_name=name, name=name)
            entity.put()

        def get_entity(name):
            return MyModel.get_by_key_name(name)

        entity = ext_db.run_in_namespace('ns1', get_entity, 'foo')
        self.assertEqual(entity, None)

        ext_db.run_in_namespace('ns1', create_entity, 'foo')

        entity = ext_db.run_in_namespace('ns1', get_entity, 'foo')
        self.assertNotEqual(entity, None)

        entity = ext_db.run_in_namespace('ns2', get_entity, 'foo')
        self.assertEqual(entity, None)
