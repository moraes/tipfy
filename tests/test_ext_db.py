# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.db
"""
import unittest
import hashlib
from nose.tools import raises

from google.appengine.ext import db
from gaetestbed import DataStoreTestCase

from tipfy import NotFound
from tipfy.ext.db import get_entity_from_protobuf, get_protobuf_from_entity, \
    populate_entity, get_by_key_name_or_404, get_by_id_or_404, get_or_404, \
    get_or_insert_with_flag, get_reference_key, PickleProperty, SlugProperty, \
    EtagProperty, retry_on_timeout, load_entity


class FooModel(db.Model):
    name = db.StringProperty(required=True)
    name2 = db.StringProperty()
    age = db.IntegerProperty()
    married = db.BooleanProperty()
    data = PickleProperty()
    slug = SlugProperty(name)
    slug2 = SlugProperty(name2, default='some-default-value', max_length=20)
    etag = EtagProperty(name)
    etag2 = EtagProperty(name2)


class FooExpandoModel(db.Expando):
    pass


class BarModel(db.Model):
    foo = db.ReferenceProperty(FooModel)


@retry_on_timeout(retries=3, interval=0.1)
def test_timeout_1(**kwargs):
    counter = kwargs.get('counter')

    # Let it pass only in the last attempt
    if counter[0] < 3:
        counter[0] += 1
        raise db.Timeout()


@retry_on_timeout(retries=5, interval=0.1)
def test_timeout_2(**kwargs):
    counter = kwargs.get('counter')

    # Let it pass only in the last attempt
    if counter[0] < 5:
        counter[0] += 1
        raise db.Timeout()

    raise ValueError()


@retry_on_timeout(retries=2, interval=0.1)
def test_timeout_3(**kwargs):
    # Never let it pass.
    counter = kwargs.get('counter')
    counter[0] += 1
    raise db.Timeout()


class TestModel(DataStoreTestCase, unittest.TestCase):
    def test_no_protobuf_from_entity(self):
        res_1 = get_protobuf_from_entity([])
        self.assertEqual(res_1, None)
        res_2 = get_protobuf_from_entity(None)
        self.assertEqual(res_2, None)

    def test_no_entity_from_protobuf(self):
        res_1 = get_entity_from_protobuf([])
        self.assertEqual(res_1, None)
        res_2 = get_entity_from_protobuf(None)
        self.assertEqual(res_2, None)

    def test_one_model_to_and_from_protobuf(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        pb_1 = get_protobuf_from_entity(entity_1)

        entity_1 = get_entity_from_protobuf(pb_1)
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

        pbs = get_protobuf_from_entity([entity_1, entity_2, entity_3])
        self.assertEqual(len(pbs), 3)

        entity_1, entity_2, entity_3 = get_entity_from_protobuf(pbs)
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
        self.assertEqual(str(get_reference_key(entity_3, 'foo')), entity_1_key)

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
        self.assertEqual(str(get_reference_key(fetched_book, 'author')), str(author.key()))

    #===========================================================================
    # populate_entity
    #===========================================================================
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

    @raises(AttributeError)
    def test_populate_entity_2(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

        populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        getattr(entity_1, 'city')

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

    @raises(AttributeError)
    def test_populate_expando_entity_2(self):
        entity_1 = FooExpandoModel(name='foo', age=15, married=False)
        entity_1.put()

        self.assertEqual(entity_1.name, 'foo')
        self.assertEqual(entity_1.age, 15)
        self.assertEqual(entity_1.married, False)

        populate_entity(entity_1, name='bar', age=20, married=True, city='Yukon')
        entity_1.put()

        getattr(entity_1, 'city')

    #===========================================================================
    # get..._or_404
    #===========================================================================
    def test_get_by_key_name_or_404(self):
        entity_1 = FooModel(key_name='foo', name='foo', age=15, married=False)
        entity_1.put()

        entity = get_by_key_name_or_404(FooModel, 'foo')
        self.assertEqual(str(entity.key()), str(entity_1.key()))

    @raises(NotFound)
    def test_get_by_key_name_or_404_2(self):
        get_by_key_name_or_404(FooModel, 'bar')

    def test_get_by_id_or_404(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        entity = get_by_id_or_404(FooModel, entity_1.key().id())
        self.assertEqual(str(entity.key()), str(entity_1.key()))

    @raises(NotFound)
    def test_get_by_id_or_404_2(self):
        get_by_id_or_404(FooModel, -1)

    def test_get_or_404(self):
        entity_1 = FooModel(name='foo', age=15, married=False)
        entity_1.put()

        entity = get_or_404(FooModel, entity_1.key())
        self.assertEqual(str(entity.key()), str(entity_1.key()))

    @raises(NotFound)
    def test_get_or_404_2(self):
        get_or_404(FooModel, db.Key.from_path('FooModel', 'bar'))

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

    #===========================================================================
    # @retry_on_timeout
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
    # @load_entity
    #===========================================================================
    def test_load_entity_with_key(self):
        @load_entity(FooModel, 'foo_key', 'foo', 'key')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(name='foo')
        foo.put()

        loaded_foo = get(foo_key=str(foo.key()))
        self.assertEqual(str(loaded_foo.key()), str(foo.key()))
        self.assertEqual(get(foo_key=None), None)

    @raises(NotFound)
    def test_load_entity_with_key_2(self):
        @load_entity(FooModel, 'foo_key', 'foo', 'key')
        def get(*args, **kwargs):
            return kwargs['foo']

        loaded_foo = get(foo_key=str(db.Key.from_path('FooModel', 'bar')))

    def test_load_entity_with_id(self):
        @load_entity(FooModel, 'foo_id', 'foo', 'id')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(name='foo')
        foo.put()

        loaded_foo = get(foo_id=foo.key().id())
        self.assertEqual(str(loaded_foo.key()), str(foo.key()))

    @raises(NotFound)
    def test_load_entity_with_id_2(self):
        @load_entity(FooModel, 'foo_id', 'foo', 'id')
        def get(*args, **kwargs):
            return kwargs['foo']

        loaded_foo = get(foo_id=-1)

    def test_load_entity_with_key_name(self):
        @load_entity(FooModel, 'foo_key_name', 'foo', 'key_name')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(key_name='foo', name='foo')
        foo.put()

        loaded_foo = get(foo_key_name='foo')
        self.assertEqual(str(loaded_foo.key()), str(foo.key()))

    @raises(NotFound)
    def test_load_entity_with_key_name_2(self):
        @load_entity(FooModel, 'foo_key_name', 'foo', 'key_name')
        def get(*args, **kwargs):
            return kwargs['foo']

        loaded_foo = get(foo_key_name='bar')

    def test_load_entity_with_key_with_guessed_fetch_mode(self):
        @load_entity(FooModel, 'foo_key')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(name='foo')
        foo.put()

        loaded_foo = get(foo_key=str(foo.key()))
        self.assertEqual(str(loaded_foo.key()), str(foo.key()))
        self.assertEqual(get(foo_key=None), None)

    @raises(NotImplementedError)
    def test_load_entity_with_key_with_impossible_fetch_mode(self):
        @load_entity(FooModel, 'foo_bar')
        def get(*args, **kwargs):
            return kwargs['foo']

        foo = FooModel(name='foo')
        foo.put()

        loaded_foo = get(foo_key=str(foo.key()))
        self.assertEqual(str(loaded_foo.key()), str(foo.key()))
        self.assertEqual(get(foo_key=None), None)
