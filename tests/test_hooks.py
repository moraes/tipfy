# -*- coding: utf-8 -*-
"""
    Tests for tipfy.HookHandler and tipfy.LazyCallable.
"""
import unittest
from types import FunctionType

from _base import get_app, get_environ, get_request, get_response
from tipfy import HookHandler, LazyCallable


def event_callable_1(name):
    return name + 'something_added'

def event_callable_2(name):
    return name + 'something_added_2'

def event_callable_3(name):
    return name + 'something_added_3'

def event_callable_4(name):
    return name + 'something_added_4'


class TestLazyCallable(unittest.TestCase):
    def test_hook_init(self):
        hook_spec = 'foo'
        event_hook = LazyCallable(hook_spec)
        assert event_hook.hook_spec == hook_spec
        assert event_hook.hook is None

    def test_hook_call(self):
        hook_spec = '%s:event_callable_1' % __name__
        event_hook = LazyCallable(hook_spec)

        assert event_hook('foo') == 'foo' + 'something_added'
        assert event_hook('bar') == 'bar' + 'something_added'
        assert event_hook('baz') == 'baz' + 'something_added'


class TestHookHandler(unittest.TestCase):
    def test_add(self):
        hook_handler = HookHandler()

        hook_handler.add('before_request_init', 'foo')
        hook_handler.add('before_request_init', 'bar')
        hook_handler.add('after_request_init', 'baz')
        hook_handler.add('after_request_dispatch', 'ding')

        event_1 = hook_handler.hooks.get('before_request_init', None)
        assert len(event_1) == 2
        for event in event_1:
            assert isinstance(event, LazyCallable)

        assert event_1[0].hook_spec == 'foo'
        assert event_1[1].hook_spec == 'bar'

        event_2 = hook_handler.hooks.get('after_request_init', None)
        assert len(event_2) == 1
        for event in event_2:
            assert isinstance(event, LazyCallable)

        assert event_2[0].hook_spec == 'baz'

        event_3 = hook_handler.hooks.get('after_request_dispatch', None)
        assert len(event_3) == 1
        for event in event_3:
            assert isinstance(event, LazyCallable)

        assert event_3[0].hook_spec == 'ding'

    def test_add_callable(self):
        hook_handler = HookHandler()

        hook_handler.add('before_request_init', event_callable_1)
        hook_handler.add('before_request_init', event_callable_2)
        hook_handler.add('after_request_init', event_callable_3)
        hook_handler.add('after_request_dispatch', event_callable_4)

        event_1 = hook_handler.hooks.get('before_request_init', None)
        assert len(event_1) == 2
        for event in event_1:
            assert isinstance(event, FunctionType)

        assert event_1[0].__name__ == 'event_callable_1'
        assert event_1[1].__name__ == 'event_callable_2'

        event_2 = hook_handler.hooks.get('after_request_init', None)
        assert len(event_2) == 1
        for event in event_2:
            assert isinstance(event, FunctionType)

        assert event_2[0].__name__ == 'event_callable_3'

        event_3 = hook_handler.hooks.get('after_request_dispatch', None)
        assert len(event_3) == 1
        for event in event_3:
            assert isinstance(event, FunctionType)

        assert event_3[0].__name__ == 'event_callable_4'

    def test_add_multi(self):
        hook_handler = HookHandler()

        hook_handler.add_multi({
            'before_request_init': ['foo', 'bar'],
            'after_request_init': ['baz'],
            'after_request_dispatch': ['ding'],
        })

        event_1 = hook_handler.hooks.get('before_request_init', None)
        assert len(event_1) == 2
        for event in event_1:
            assert isinstance(event, LazyCallable)

        assert event_1[0].hook_spec == 'foo'
        assert event_1[1].hook_spec == 'bar'

        event_2 = hook_handler.hooks.get('after_request_init', None)
        assert len(event_2) == 1
        for event in event_2:
            assert isinstance(event, LazyCallable)

        assert event_2[0].hook_spec == 'baz'

        event_3 = hook_handler.hooks.get('after_request_dispatch', None)
        assert len(event_3) == 1
        for event in event_3:
            assert isinstance(event, LazyCallable)

        assert event_3[0].hook_spec == 'ding'

    def test_add_multi_with_callable(self):
        hook_handler = HookHandler()

        hook_handler.add_multi({
            'before_request_init': ['foo', 'bar'],
            'after_request_init': [event_callable_1],
            'after_request_dispatch': ['ding'],
        })

        event_1 = hook_handler.hooks.get('before_request_init', None)
        assert len(event_1) == 2
        for event in event_1:
            assert isinstance(event, LazyCallable)

        assert event_1[0].hook_spec == 'foo'
        assert event_1[1].hook_spec == 'bar'

        event_2 = hook_handler.hooks.get('after_request_init', None)
        assert len(event_2) == 1
        for event in event_2:
            assert isinstance(event, FunctionType)

        assert event_2[0].__name__ == 'event_callable_1'

        event_3 = hook_handler.hooks.get('after_request_dispatch', None)
        assert len(event_3) == 1
        for event in event_3:
            assert isinstance(event, LazyCallable)

        assert event_3[0].hook_spec == 'ding'

    def test_call(self):
        hook_handler = HookHandler()

        hook_handler.add('before_request_init', '%s:event_callable_1' % __name__)

        hook_handler.add_multi({
            'before_request_init': ['%s:event_callable_2' % __name__],
            'after_request_init': ['%s:event_callable_3' % __name__],
            'after_request_dispatch': ['%s:event_callable_4' % __name__],
        })

        hook_handler.add('before_request_init', '%s:event_callable_1' % __name__)

        i = 0
        name = 'something'
        expected_results = [
            name + 'something_added',
            name + 'something_added_2',
            name + 'something_added',
        ]
        for result in hook_handler.call('before_request_init', name):
            assert result == expected_results[i]
            i += 1

        assert i == 3

        i = 0
        name = 'something2'
        expected_results = [
            name + 'something_added_3',
        ]
        for result in hook_handler.call('after_request_init', name):
            assert result == expected_results[i]
            i += 1

        assert i == 1

        i = 0
        name = 'something2'
        expected_results = [
            name + 'something_added_4',
        ]
        for result in hook_handler.call('after_request_dispatch', name):
            assert result == expected_results[i]
            i += 1

        assert i == 1

    def test_call_with_callable(self):
        hook_handler = HookHandler()

        hook_handler.add('before_request_init', '%s:event_callable_1' % __name__)

        hook_handler.add_multi({
            'before_request_init': ['%s:event_callable_2' % __name__],
            'after_request_init': ['%s:event_callable_3' % __name__],
            'after_request_dispatch': [event_callable_4],
        })

        hook_handler.add('before_request_init', '%s:event_callable_1' % __name__)

        i = 0
        name = 'something'
        expected_results = [
            name + 'something_added',
            name + 'something_added_2',
            name + 'something_added',
        ]
        for result in hook_handler.call('before_request_init', name):
            assert result == expected_results[i]
            i += 1

        assert i == 3

        i = 0
        name = 'something2'
        expected_results = [
            name + 'something_added_3',
        ]
        for result in hook_handler.call('after_request_init', name):
            assert result == expected_results[i]
            i += 1

        assert i == 1

        i = 0
        name = 'something2'
        expected_results = [
            name + 'something_added_4',
        ]
        for result in hook_handler.call('after_request_dispatch', name):
            assert result == expected_results[i]
            i += 1

        assert i == 1

    def test_iter(self):
        hook_handler = HookHandler()

        hook_handler.add('before_request_init', '%s:event_callable_1' % __name__)

        hook_handler.add_multi({
            'before_request_init': ['%s:event_callable_2' % __name__],
            'after_request_init': ['%s:event_callable_3' % __name__],
            'after_request_dispatch': ['%s:event_callable_4' % __name__],
        })

        hook_handler.add('before_request_init', '%s:event_callable_1' % __name__)

        i = 0
        name = 'something'
        expected_results = [
            name + 'something_added',
            name + 'something_added_2',
            name + 'something_added',
        ]
        for result in hook_handler.iter('before_request_init', name):
            assert result == expected_results[i]
            i += 1

        assert i == 3

        i = 0
        name = 'something2'
        expected_results = [
            name + 'something_added_3',
        ]
        for result in hook_handler.iter('after_request_init', name):
            assert result == expected_results[i]
            i += 1

        assert i == 1

        i = 0
        name = 'something2'
        expected_results = [
            name + 'something_added_4',
        ]
        for result in hook_handler.iter('after_request_dispatch', name):
            assert result == expected_results[i]
            i += 1

        assert i == 1

    def test_iter_with_callable(self):
        hook_handler = HookHandler()

        hook_handler.add('before_request_init', '%s:event_callable_1' % __name__)

        hook_handler.add_multi({
            'before_request_init': ['%s:event_callable_2' % __name__],
            'after_request_init': [event_callable_3],
            'after_request_dispatch': ['%s:event_callable_4' % __name__],
        })

        hook_handler.add('before_request_init', '%s:event_callable_1' % __name__)

        i = 0
        name = 'something'
        expected_results = [
            name + 'something_added',
            name + 'something_added_2',
            name + 'something_added',
        ]
        for result in hook_handler.iter('before_request_init', name):
            assert result == expected_results[i]
            i += 1

        assert i == 3

        i = 0
        name = 'something2'
        expected_results = [
            name + 'something_added_3',
        ]
        for result in hook_handler.iter('after_request_init', name):
            assert result == expected_results[i]
            i += 1

        assert i == 1

        i = 0
        name = 'something2'
        expected_results = [
            name + 'something_added_4',
        ]
        for result in hook_handler.iter('after_request_dispatch', name):
            assert result == expected_results[i]
            i += 1

        assert i == 1
