# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.db
"""
import unittest
import hashlib
from nose.tools import raises, assert_raises

from google.appengine.ext import db
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError
from gaetestbed import DataStoreTestCase

import _base

import tipfy
from tipfy import NotFound
from tipfy.ext import db as ext_db


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
    def tearDown(self):
        tipfy.local_manager.cleanup()

    def test_no_protobuf_from_entity(self):
        res_1 = ext_db.get_entity_from_protobuf([])
        assert res_1 is None
        res_2 = ext_db.get_protobuf_from_entity(None)
        assert res_2 is None

    def test_no_entity_from_protobuf(self):
        res_1 = ext_db.get_entity_from_protobuf([])
        assert res_1 is None

    def test_one_model_to_and_from_protobuf(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        pb_1 = ext_db.get_protobuf_from_entity(entity_1)

        entity_1 = ext_db.get_entity_from_protobuf(pb_1)
        assert isinstance(entity_1, FooModel)
        assert entity_1.name == 'foo'
        assert entity_1.age == 15
        assert entity_1.married is False

    def test_many_models_to_and_from_protobuf(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()
        entity_2 = FooModel(name='bar', age=30, married=True)
        entity_2.put()
        entity_3 = FooModel(name='baz', age=45, married=False)
        entity_3.put()

        pbs = ext_db.get_protobuf_from_entity([entity_1, entity_2, entity_3])
        assert len(pbs) == 3

        entity_1, entity_2, entity_3 = ext_db.get_entity_from_protobuf(pbs)
        assert isinstance(entity_1, FooModel)
        assert entity_1.name == 'foo'
        assert entity_1.age == 15
        assert entity_1.married is False

        assert isinstance(entity_2, FooModel)
        assert entity_2.name == 'bar'
        assert entity_2.age == 30
        assert entity_2.married is True

        assert isinstance(entity_3, FooModel)
        assert entity_3.name == 'baz'
        assert entity_3.age == 45
        assert entity_3.married is False

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

        assert isinstance(entity_1, FooModel)
        assert entity_1.name == 'foo'
        assert entity_1.age == 15
        assert entity_1.married is False

        assert isinstance(entity_2, FooModel)
        assert entity_2.name == 'bar'
        assert entity_2.age == 30
        assert entity_2.married is True

        assert isinstance(entity_3, FooModel)
        assert entity_3.name == 'baz'
        assert entity_3.age == 45
        assert entity_3.married is False

    def test_get_or_insert_with_flag(self):
        entity, flag = ext_db.get_or_insert_with_flag(FooModel, 'foo', name='foo', age=15, married=False)
        assert flag is True
        assert entity.name == 'foo'
        assert entity.age == 15
        assert entity.married is False

        entity, flag = ext_db.get_or_insert_with_flag(FooModel, 'foo', name='bar', age=30, married=True)
        assert flag is False
        assert entity.name == 'foo'
        assert entity.age == 15
        assert entity.married is False

    def test_get_reference_key(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()
        entity_1_key = str(entity_1.key())

        entity_2 = BarModel(key_name='first_bar', foo=entity_1)
        entity_2.put()

        entity_1.delete()
        entity_3 = BarModel.get_by_key_name('first_bar')
        # Won't resolve, but we can still get the key value.
        assert_raises(db.Error, getattr, entity_3, 'foo')
        assert str(ext_db.get_reference_key(entity_3, 'foo')) == entity_1_key

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
        assert str(ext_db.get_reference_key(fetched_book, 'author')) == str(author.key())

    #===========================================================================
    # ext_db.populate_entity
    #===========================================================================
    def test_populate_entity(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        assert entity_1.name == 'foo'
        assert entity_1.age == 15
        assert entity_1.married is False

        ext_db.populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        assert entity_1.name == 'bar'
        assert entity_1.age == 20
        assert entity_1.married is True

    @raises(AttributeError)
    def test_populate_entity_2(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        assert entity_1.name == 'foo'
        assert entity_1.age == 15
        assert entity_1.married is False

        ext_db.populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        getattr(entity_1, 'city')

    def test_populate_expando_entity(self):
        entity_1 = FooExpandoModel(name='foo', age=15, married=False)
        entity_1.put()

        assert entity_1.name == 'foo'
        assert entity_1.age == 15
        assert entity_1.married is False

        ext_db.populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        assert entity_1.name == 'bar'
        assert entity_1.age == 20
        assert entity_1.married is True

    @raises(AttributeError)
    def test_populate_expando_entity_2(self):
        entity_1 = FooExpandoModel(name='foo', age=15, married=False)
        entity_1.put()

        assert entity_1.name == 'foo'
        assert entity_1.age == 15
        assert entity_1.married is False

        ext_db.populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        getattr(entity_1, 'city')


    #===========================================================================
    # ext_db.get_property_dict
    #===========================================================================
    def test_get_property_dict(self):
        class MyModel(db.Model):
            animal = db.StringProperty()
            species = db.IntegerProperty()
            description = db.TextProperty()

        entity = MyModel(animal='duck', species=12,
            description='A duck is a bird that swims well.')
        values = ext_db.get_property_dict(entity)

        assert values == {
            'animal': 'duck',
            'species': 12,
            'description': 'A duck is a bird that swims well.',
        }

    def test_get_property_dict_with_expando(self):
        class MyModel(db.Expando):
            animal = db.StringProperty()
            species = db.IntegerProperty()
            description = db.TextProperty()

        entity = MyModel(animal='duck', species=12,
            description='A duck is a bird that swims well.',
            most_famous='Daffy Duck')
        values = ext_db.get_property_dict(entity)

        assert values == {
            'animal': 'duck',
            'species': 12,
            'description': 'A duck is a bird that swims well.',
            'most_famous': 'Daffy Duck',
        }

    #===========================================================================
    # get..._or_404
    #===========================================================================
    def test_get_by_key_name_or_404(self):
        entity_1 = FooModel(key_name='foo', name='foo', age=15, married=False)
        entity_1.put()

        entity = ext_db.get_by_key_name_or_404(FooModel, 'foo')
        assert str(entity.key()) == str(entity_1.key())

    @raises(NotFound)
    def test_get_by_key_name_or_404_2(self):
        ext_db.get_by_key_name_or_404(FooModel, 'bar')

    def test_get_by_id_or_404(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        entity = ext_db.get_by_id_or_404(FooModel, entity_1.key().id())
        assert str(entity.key()) == str(entity_1.key())

    @raises(NotFound)
    def test_get_by_id_or_404_2(self):
        ext_db.get_by_id_or_404(FooModel, -1)

    def test_get_or_404(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        entity = ext_db.get_or_404(FooModel, entity_1.key())
        assert str(entity.key()) == str(entity_1.key())

    @raises(NotFound)
    def test_get_or_404_2(self):
        ext_db.get_or_404(FooModel, db.Key.from_path('FooModel', 'bar'))

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
        assert entity_1.data == data_1

        entity_2 = FooModel.get_by_key_name('bar')
        assert entity_2.data == data_2

    def test_slug_property(self):
        entity_1 = FooModel(key_name='foo', name=u'Mary Björk')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'Tião Macalé')
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        assert entity_1.slug == 'mary-bjork'
        assert entity_2.slug == 'tiao-macale'

    def test_slug_property2(self):
        entity_1 = FooModel(key_name='foo', name=u'---')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'___')
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        assert entity_1.slug is None
        assert entity_2.slug is None

    def test_slug_property3(self):
        entity_1 = FooModel(key_name='foo', name=u'---', name2=u'---')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'___', name2=u'___')
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        assert entity_1.slug2 == 'some-default-value'
        assert entity_2.slug2 == 'some-default-value'

    def test_slug_property4(self):
        entity_1 = FooModel(key_name='foo', name=u'---', name2=u'Some really very big and maybe enormous string')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'___', name2=u'abcdefghijklmnopqrstuwxyz')
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        assert entity_1.slug2 == 'some-really-very-big'
        assert entity_2.slug2 == 'abcdefghijklmnopqrst'

    def test_etag_property(self):
        entity_1 = FooModel(key_name='foo', name=u'Mary Björk')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'Tião Macalé')
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        assert entity_1.etag == hashlib.sha1(entity_1.name.encode('utf8')).hexdigest()
        assert entity_2.etag == hashlib.sha1(entity_2.name.encode('utf8')).hexdigest()

    def test_etag_property2(self):
        entity_1 = FooModel(key_name='foo', name=u'Mary Björk')
        entity_1.put()

        entity_2 = FooModel(key_name='bar', name=u'Tião Macalé')
        entity_2.put()

        entity_1 = FooModel.get_by_key_name('foo')
        entity_2 = FooModel.get_by_key_name('bar')
        assert entity_1.etag2 is None
        assert entity_2.etag2 is None

    def test_json_property(self):
        entity_1 = JsonModel(key_name='foo', data={'foo': 'bar'})
        entity_1.put()

        entity_1 = JsonModel.get_by_key_name('foo')
        assert entity_1.data == {'foo': 'bar'}

    @raises(db.BadValueError)
    def test_json_property2(self):
        entity_1 = JsonModel(key_name='foo', data='foo')
        entity_1.put()

        entity_1 = JsonModel.get_by_key_name('foo')
        assert entity_1.data == {'foo': 'bar'}

    def test_timezone_property(self):
        zone = 'America/Chicago'
        entity_1 = TimezoneModel(key_name='foo', data=zone)
        entity_1.put()

        entity_1 = TimezoneModel.get_by_key_name('foo')
        assert entity_1.data == ext_db.pytz.timezone(zone)

    @raises(db.BadValueError)
    def test_timezone_property2(self):
        zone = 'foo'
        entity_1 = TimezoneModel(key_name='foo', data=[])
        entity_1.put()

    @raises(ext_db.pytz.UnknownTimeZoneError)
    def test_timezone_property3(self):
        entity_1 = TimezoneModel(key_name='foo', data='foo')
        entity_1.put()

        entity_1 = TimezoneModel.get_by_key_name('foo')
        assert entity_1.data == {'foo': 'bar'}

    #===========================================================================
    # @ext_db.retry_on_timeout
    #===========================================================================
    def test_retry_on_timeout_1(self):
        counter = [0]
        test_timeout_1(counter=counter)
        assert counter[0] == 3

    def test_retry_on_timeout_2(self):
        counter = [0]
        assert_raises(ValueError, test_timeout_2, counter=counter)
        assert counter[0] == 5

    def test_retry_on_timeout_3(self):
        counter = [0]
        assert_raises(db.Timeout, test_timeout_3, counter=counter)
        assert counter[0] == 3

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
        assert str(loaded_foo.key()) == str(foo.key())
        assert get(foo_key=None) is None

    @raises(NotFound)
    def test_load_entity_with_key_2(self):
        @ext_db.load_entity(FooModel, 'foo_key', 'foo', 'key')
        def get(*args, **kwargs):
            return kwargs['foo']

        loaded_foo = get(foo_key=str(db.Key.from_path('FooModel', 'bar')))

    def test_load_entity_with_id(self):
        @ext_db.load_entity(FooModel, 'foo_id', 'foo', 'id')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(name='foo')
        foo.put()

        loaded_foo = get(foo_id=foo.key().id())
        assert str(loaded_foo.key()) == str(foo.key())

    @raises(NotFound)
    def test_load_entity_with_id_2(self):
        @ext_db.load_entity(FooModel, 'foo_id', 'foo', 'id')
        def get(*args, **kwargs):
            return kwargs['foo']

        loaded_foo = get(foo_id=-1)

    def test_load_entity_with_key_name(self):
        @ext_db.load_entity(FooModel, 'foo_key_name', 'foo', 'key_name')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(key_name='foo', name='foo')
        foo.put()

        loaded_foo = get(foo_key_name='foo')
        assert str(loaded_foo.key()) == str(foo.key())

    @raises(NotFound)
    def test_load_entity_with_key_name_2(self):
        @ext_db.load_entity(FooModel, 'foo_key_name', 'foo', 'key_name')
        def get(*args, **kwargs):
            return kwargs['foo']

        loaded_foo = get(foo_key_name='bar')

    def test_load_entity_with_key_with_guessed_fetch_mode(self):
        @ext_db.load_entity(FooModel, 'foo_key')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(name='foo')
        foo.put()

        loaded_foo = get(foo_key=str(foo.key()))
        assert str(loaded_foo.key()) == str(foo.key())
        assert get(foo_key=None) is None

    @raises(NotImplementedError)
    def test_load_entity_with_key_with_impossible_fetch_mode(self):
        @ext_db.load_entity(FooModel, 'foo_bar')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(name='foo')
        foo.put()

        loaded_foo = get(foo_key=str(foo.key()))
        assert str(loaded_foo.key()) == str(foo.key())
        assert get(foo_key=None) is None
