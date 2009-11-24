# -*- coding: utf-8 -*-
"""
    Tests for tipfy.EventHandler and tipfy.EventManager.
"""
import unittest
import sys
from _base import get_app, get_environ, get_request, get_response


from tipfy import Config


class TestConfig(unittest.TestCase):
    def test_get(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config.get('bar'), None)
        self.assertEqual(config.get('foo'), {
            'bar': 'baz',
            'doo': 'ding',
        })

        self.assertEqual(config.get('foo', 'bar'), 'baz')
        self.assertEqual(config.get('foo', 'doo'), 'ding')
        self.assertEqual(config.get('foo', 'hmm'), None)
        self.assertEqual(config.get('foo', 'hmm', 'default'), 'default')

    def test_update(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config['foo']['bar'], 'baz')
        self.assertEqual(config['foo']['doo'], 'ding')

        config.update({'foo': {'bar': 'other',}})

        self.assertEqual(config['foo']['bar'], 'other')
        self.assertEqual(config['foo']['doo'], 'ding')

    def test_setdefault(self):
        config = Config()

        self.assertEqual(config.get('foo'), None)

        config.setdefault('foo', {
            'bar': 'baz',
            'doo': 'ding',
        })

        self.assertEqual(config['foo']['bar'], 'baz')
        self.assertEqual(config['foo']['doo'], 'ding')

