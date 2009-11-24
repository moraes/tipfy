# -*- coding: utf-8 -*-
"""
    Tests for tipfy.EventHandler and tipfy.EventManager.
"""
import unittest
import sys
from _base import get_app, get_environ, get_request, get_response


from tipfy import EventHandler, EventManager


def event_callable_1(name):
    return name + 'something_added'

def event_callable_2(name):
    return name + 'something_added_2'

def event_callable_3(name):
    return name + 'something_added_3'

def event_callable_4(name):
    return name + 'something_added_4'


class TestEventHandler(unittest.TestCase):
    def test_handler_init(self):
        handler_spec = 'foo'
        event_handler = EventHandler(handler_spec)
        self.assertEqual(event_handler.handler_spec, handler_spec)
        self.assertEqual(event_handler.handler, None)

    def test_handler_call(self):
        handler_spec = '%s:event_callable_1' % __name__
        event_handler = EventHandler(handler_spec)

        self.assertEqual(event_handler('foo'), 'foo' + 'something_added')
        self.assertEqual(event_handler('bar'), 'bar' + 'something_added')
        self.assertEqual(event_handler('baz'), 'baz' + 'something_added')


class TestEventManager(unittest.TestCase):
    def test_subscribe(self):
        event_manager = EventManager()

        event_manager.subscribe('before_request_init', 'foo')
        event_manager.subscribe('before_request_init', 'bar')
        event_manager.subscribe('after_request_init', 'baz')
        event_manager.subscribe('after_request_dispatch', 'ding')

        event_1 = event_manager.subscribers.get('before_request_init', None)
        self.assertEqual(len(event_1), 2)
        for event in event_1:
            self.assertEqual(isinstance(event, EventHandler), True)

        self.assertEqual(event_1[0].handler_spec, 'foo')
        self.assertEqual(event_1[1].handler_spec, 'bar')

        event_2 = event_manager.subscribers.get('after_request_init', None)
        self.assertEqual(len(event_2), 1)
        for event in event_2:
            self.assertEqual(isinstance(event, EventHandler), True)

        self.assertEqual(event_2[0].handler_spec, 'baz')

        event_3 = event_manager.subscribers.get('after_request_dispatch', None)
        self.assertEqual(len(event_3), 1)
        for event in event_3:
            self.assertEqual(isinstance(event, EventHandler), True)

        self.assertEqual(event_3[0].handler_spec, 'ding')

    def test_subscribe_multi(self):
        event_manager = EventManager()

        event_manager.subscribe_multi({
            'before_request_init': ['foo', 'bar'],
            'after_request_init': ['baz'],
            'after_request_dispatch': ['ding'],
        })

        event_1 = event_manager.subscribers.get('before_request_init', None)
        self.assertEqual(len(event_1), 2)
        for event in event_1:
            self.assertEqual(isinstance(event, EventHandler), True)

        self.assertEqual(event_1[0].handler_spec, 'foo')
        self.assertEqual(event_1[1].handler_spec, 'bar')

        event_2 = event_manager.subscribers.get('after_request_init', None)
        self.assertEqual(len(event_2), 1)
        for event in event_2:
            self.assertEqual(isinstance(event, EventHandler), True)

        self.assertEqual(event_2[0].handler_spec, 'baz')

        event_3 = event_manager.subscribers.get('after_request_dispatch', None)
        self.assertEqual(len(event_3), 1)
        for event in event_3:
            self.assertEqual(isinstance(event, EventHandler), True)

        self.assertEqual(event_3[0].handler_spec, 'ding')

    def test_notify(self):
        event_manager = EventManager()

        event_manager.subscribe('before_request_init', '%s:event_callable_1' % __name__)

        event_manager.subscribe_multi({
            'before_request_init': ['%s:event_callable_2' % __name__],
            'after_request_init': ['%s:event_callable_3' % __name__],
            'after_request_dispatch': ['%s:event_callable_4' % __name__],
        })

        event_manager.subscribe('before_request_init', '%s:event_callable_1' % __name__)

        i = 0
        name = 'something'
        expected_results = [
            name + 'something_added',
            name + 'something_added_2',
            name + 'something_added',
        ]
        for result in event_manager.notify('before_request_init', name):
            self.assertEqual(result, expected_results[i])
            i += 1

        self.assertEqual(i, 3)

        i = 0
        name = 'something2'
        expected_results = [
            name + 'something_added_3',
        ]
        for result in event_manager.notify('after_request_init', name):
            self.assertEqual(result, expected_results[i])
            i += 1

        self.assertEqual(i, 1)

        i = 0
        name = 'something2'
        expected_results = [
            name + 'something_added_4',
        ]
        for result in event_manager.notify('after_request_dispatch', name):
            self.assertEqual(result, expected_results[i])
            i += 1

        self.assertEqual(i, 1)

    def test_iter(self):
        event_manager = EventManager()

        event_manager.subscribe('before_request_init', '%s:event_callable_1' % __name__)

        event_manager.subscribe_multi({
            'before_request_init': ['%s:event_callable_2' % __name__],
            'after_request_init': ['%s:event_callable_3' % __name__],
            'after_request_dispatch': ['%s:event_callable_4' % __name__],
        })

        event_manager.subscribe('before_request_init', '%s:event_callable_1' % __name__)

        i = 0
        name = 'something'
        expected_results = [
            name + 'something_added',
            name + 'something_added_2',
            name + 'something_added',
        ]
        for result in event_manager.iter('before_request_init', name):
            self.assertEqual(result, expected_results[i])
            i += 1

        self.assertEqual(i, 3)

        i = 0
        name = 'something2'
        expected_results = [
            name + 'something_added_3',
        ]
        for result in event_manager.iter('after_request_init', name):
            self.assertEqual(result, expected_results[i])
            i += 1

        self.assertEqual(i, 1)

        i = 0
        name = 'something2'
        expected_results = [
            name + 'something_added_4',
        ]
        for result in event_manager.iter('after_request_dispatch', name):
            self.assertEqual(result, expected_results[i])
            i += 1

        self.assertEqual(i, 1)
