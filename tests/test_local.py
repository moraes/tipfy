# -*- coding: utf-8 -*-
"""
    Tests for tipfy.local
"""
import unittest

from nose.tools import assert_raises, raises

import _base

from tipfy.local import Local, LocalProxy


class SampleObj(object):
    pass


class TestLocal(unittest.TestCase):
    def tearDown(self):
        pass

    def test_del_attr(self):
        local = Local()

        local.foo = 'bar'
        assert local.foo == 'bar'

        del local.foo
        assert getattr(local, 'foo', None) is None

    @raises(AttributeError)
    def test_del_attr_error(self):
        local = Local()
        del local.foo

    def test_iter(self):
        local = Local()
        local.foo = 'bar'
        local.baz = 'ding'

        res = {}
        for k, v in local:
            res[k] = v

        assert res == {'foo': 'bar', 'baz': 'ding'}

    def test_release(self):
        local = Local()
        local.foo = 'bar'
        local.baz = 'ding'

        assert local.foo == 'bar'
        assert local.baz == 'ding'

        local.__release_local__()

        assert getattr(local, 'foo', None) is None
        assert getattr(local, 'baz', None) is None


class TestLocalProxy(unittest.TestCase):
    def tearDown(self):
        pass

    def test_local(self):
        """Tests some proxy operations. Test borrowed from werkzeug."""
        local = Local()
        ls = local('foo')
        local.foo = foo = []

        ls.append(42)
        ls.append(23)
        ls[1:] = [1, 2, 3]
        assert foo == [42, 1, 2, 3]
        assert repr(foo) == repr(ls)
        assert foo[0] == 42
        foo += [1]
        assert list(foo) == [42, 1, 2, 3, 1]

    def test_lambda(self):
        """Tests some proxy operations. Test borrowed from werkzeug."""
        foo = []
        ls = LocalProxy(lambda: foo)
        ls.append(42)
        ls.append(23)
        ls[1:] = [1, 2, 3]
        assert foo == [42, 1, 2, 3]
        assert repr(foo) == repr(ls)
        assert foo[0] == 42
        foo += [1]
        assert list(foo) == [42, 1, 2, 3, 1]

    @raises(RuntimeError)
    def test_not_bound(self):
        """Tests some proxy operations. Test borrowed from werkzeug."""
        local = Local()
        ls = local('foo')
        ls.append(42)

    def test_dict(self):
        foo = SampleObj()
        ls = LocalProxy(lambda: foo)

        assert ls.__dict__ == foo.__dict__

    @raises(AttributeError)
    def test_not_bound_dict(self):
        """Tests some proxy operations. Test borrowed from werkzeug."""
        foo = []
        ls = LocalProxy(lambda: foo)

        x = ls.__dict__

    @raises(RuntimeError)
    def test_not_bound_dict2(self):
        """Tests some proxy operations. Test borrowed from werkzeug."""
        local = Local()
        ls = local('foo')

        # Is this expected?
        x = ls.__dict__

    def test_repr(self):
        local = Local()
        ls = local('foo')
        assert ls.__repr__() == '<LocalProxy unbound>'

    def test_nonzero(self):
        local = Local()
        ls = local('foo')

        local.foo = 1
        assert bool(ls) is True

        local.foo = 0
        assert bool(ls) is False

        ls = local('bar')
        assert bool(ls) is False

    def test_unicode(self):
        local = Local()
        ls = local('foo')

        local.foo = 1
        assert unicode(ls) == u'1'

        local.foo = 0
        assert unicode(ls) == u'0'

        ls = local('bar')
        assert unicode(ls) == '<LocalProxy unbound>'

    def test_dir(self):
        local = Local()
        ls = local('foo')
        obj = SampleObj()
        local.foo = obj

        self.assertEqual(ls.__dir__(), dir(obj))

        ls = local('bar')
        assert ls.__dir__() == []

    def test_getattr(self):
        local = Local()
        ls = local('foo')
        obj = SampleObj()
        local.foo = obj

        self.assertEqual(ls.__members__, dir(obj))

    def test_setitem(self):
        local = Local()
        ls = local('foo')
        local.foo = {}

        ls['baz'] = 'bar'
        assert local.foo['baz'] == 'bar'

    def test_delitem(self):
        local = Local()
        ls = local('foo')
        local.foo = {'foo': 'bar'}

        assert 'foo' in ls
        del ls['foo']
        assert 'foo' not in ls

    def test_delslice(self):
        local = Local()
        ls = local('foo')

        local.foo = ['a', 'b', 'c', 'd', 'e']

        del ls[3:6]
        assert ls == ['a', 'b', 'c']

